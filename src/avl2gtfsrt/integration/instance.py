import logging
import time

from datetime import datetime, timedelta
from threading import Event, Thread

from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter
from avl2gtfsrt.integration.model.types import Vehicle, VehiclePosition
from avl2gtfsrt.integration.iom.client import IomClient


class AvlDataInstance:

    def __init__(self, config: dict) -> None:
        self.id = config['id']

        self._iom: IomClient = IomClient(
            self.id,
            config['vdv435']['organisation'],
            config['vdv435']['itcs'],
            config['broker']
        )

        self._vehicles: list[Vehicle] = list()
        self._vehicle_positions: dict[any, VehiclePosition] = dict()

        # setup everything for the adapter and thread management
        if config['adapter']['type'] == 'pajgps':
            from avl2gtfsrt.integration.adapter.pajgps.adapter import PajGpsAdapter
            self._adapter: BaseAdapter = PajGpsAdapter(self.id, config['adapter'])
        else:
            raise ValueError(f"Unknown adapter type {config['adapter']} in instance \"{self.id}\"!")

        self._thread = Thread(target=self._run_internal)

        # keep track of stopping flag
        # required here for 'cooperative stopping'
        self._should_run = Event()
        self._should_run.set()

    def run(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._should_run.clear()

    def _run_internal(self) -> None:
        
        # startup IoM client
        self._iom.start()

        # main loop, run adapter logic here ...
        while self._should_run.is_set():

            try:
                # call configured adapter in order to get all current vehicle positions
                logging.info(f"{self.id}/{self.__class__.__name__}: Loading current vehicles ...")
                vehicles_result: list[Vehicle] = self._adapter.get_vehicles()

                # sync vehicle list
                # log off vehicles which are not appearing in 
                # adapters vehicle list anymore 
                for vehicle in vehicles_result:
                    if vehicle not in self._vehicles:
                        self._vehicles.append(vehicle)

                for vehicle in self._vehicles:
                    if vehicle not in vehicles_result:
                        logging.info(f"{self.id}/{self.__class__.__name__}: Vehicle \"{vehicle.vehicle_ref}\" disappeared.")
                        logging.info(f"{self.id}/{self.__class__.__name__}: Logging off vehicle \"{vehicle.vehicle_ref}\" ...")
                        
                        self._vehicles.remove(vehicle)
                        del self._vehicle_positions[vehicle]
                        
                        if vehicle.is_logged_on:
                            try:
                                self._iom.log_off_vehicle(vehicle)
                            except Exception as ex:
                                logging.error(ex)

                # load and process vehicle positions for all vehicles
                # log on vehicles if they have delivered new data
                # log off vehicles which have not delivered data for the last 60 minutes
                logging.info(f"{self.id}/{self.__class__.__name__}: Loading current vehicle positions of {len(vehicles_result)} vehicles ...")
                vehicle_positions_result: list[VehiclePosition] = self._adapter.get_vehicle_positions()
                vehicle_positions_published: bool = False

                for vehicle_position in vehicle_positions_result:
                    reference_timestamp: int = int((datetime.now() - timedelta(seconds=self._adapter.autologoff)).timestamp())
                    last_vehicle_position: VehiclePosition|None = self._vehicle_positions[vehicle_position.vehicle.id] if vehicle_position.vehicle.id in self._vehicle_positions else None

                    if vehicle_position.timestamp >= reference_timestamp and (last_vehicle_position is None or vehicle_position.latitude != last_vehicle_position.latitude or vehicle_position.longitude != last_vehicle_position.longitude):
                        if not vehicle_position.vehicle.is_logged_on:
                            try:
                                logging.info(f"{self.id}/{self.__class__.__name__}: Logging on vehicle \"{vehicle.vehicle_ref}\" ...")
                                
                                self._iom.log_on_vehicle(vehicle_position.vehicle)
                                vehicle_position.vehicle.is_logged_on = True
                            except Exception as ex:
                                logging.error(ex)

                                continue
                        
                        logging.info(f"{self.id}/{self.__class__.__name__}: Publishing GNSS position update for vehicle \"{vehicle.vehicle_ref}\" ...")
                        self._iom.publish_gnss_position_update(vehicle_position)

                        self._vehicle_positions[vehicle_position.vehicle.id] = vehicle_position 

                        vehicle_positions_published = True
                        
                    elif vehicle_position.timestamp < reference_timestamp and vehicle_position.vehicle.is_logged_on:
                        try:
                            logging.info(f"{self.id}/{self.__class__.__name__}: Logging off vehicle \"{vehicle.vehicle_ref}\" ...")
                                
                            self._iom.log_off_vehicle(vehicle_position.vehicle)
                            vehicle_position.vehicle.is_logged_on = False
                        except Exception as ex:
                            logging.error(ex)

                if not vehicle_positions_published:
                    logging.info(f"{self.id}/{self.__class__.__name__}: No actual vehicle positions found.")

            except Exception as ex:
                logging.error(ex)
            finally:
                # wait for the adapter configured timespan until the next request
                time.sleep(self._adapter.interval)

        # shutdown the instance here ...
        # log off all actively monitored vehicles
        for vehicle in self._vehicles:
            if vehicle.is_logged_on:
                try:
                    logging.info(f"{self.id}/{self.__class__.__name__}: Logging off vehicle \"{vehicle.vehicle_ref}\" ...")
                    self._iom.log_off_vehicle(vehicle)
                except Exception as ex:
                    logging.error(ex)

        self._iom.terminate()