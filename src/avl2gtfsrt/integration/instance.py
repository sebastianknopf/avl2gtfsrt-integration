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
        self._vehicle_blacklist: list[Vehicle] = list()

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

                # log on and add newly discovered vehicles ...
                for vehicle in vehicles_result:
                    if vehicle not in self._vehicles or vehicle in self._vehicle_blacklist:
                        logging.debug(f"{self.id}/{self.__class__.__name__}: Vehicle \"{vehicle.vehicle_ref}\" discovered.")
                        logging.info(f"{self.id}/{self.__class__.__name__}: Logging on vehicle \"{vehicle.vehicle_ref}\" ...")

                        try:
                            self._iom.log_on_vehicle(vehicle)

                            self._vehicles.append(vehicle)

                            # remove vehicle from blacklist, in order to allow further messages
                            if vehicle in self._vehicle_blacklist:
                                self._vehicle_blacklist.remove(vehicle)
                        except Exception as ex:
                            logging.error(ex)

                            # add vehicle to blacklist in order to suppress further messages
                            if vehicle not in self._vehicle_blacklist:
                                self._vehicle_blacklist.append(vehicle)

                # log off and remove disappeared vehicles ...
                for vehicle in self._vehicles:
                    if vehicle not in vehicles_result:
                        logging.debug(f"{self.id}/{self.__class__.__name__}: Vehicle \"{vehicle.vehicle_ref}\" disappeared.")
                        logging.info(f"{self.id}/{self.__class__.__name__}: Logging off vehicle \"{vehicle.vehicle_ref}\" ...")
                        
                        self._vehicles.remove(vehicle)
                        del self._vehicle_positions[vehicle]

                        if vehicle in self._vehicle_blacklist:
                            self._vehicle_blacklist.remove(vehicle)
                        
                        try:
                            self._iom.log_off_vehicle(vehicle)
                        except Exception as ex:
                            logging.error(ex)

                # load and process vehicle positions for all vehicles
                logging.info(f"{self.id}/{self.__class__.__name__}: Loading current vehicle positions of {len(vehicles_result)} vehicles ...")
                vehicle_positions_result: list[VehiclePosition] = self._adapter.get_vehicle_positions()

                for vehicle_position in vehicle_positions_result:
                    if vehicle_position.vehicle not in self._vehicle_blacklist:
                        reference_timestamp: int = int((datetime.now() - timedelta(seconds=150)).timestamp())
                        last_vehicle_position: VehiclePosition|None = self._vehicle_positions[vehicle_position.vehicle.id] if vehicle_position.vehicle.id in self._vehicle_positions else None
                        
                        if vehicle_position.timestamp >= reference_timestamp and (last_vehicle_position is None or vehicle_position.latitude != last_vehicle_position.latitude or vehicle_position.longitude != last_vehicle_position.longitude):
                            logging.info(f"{self.id}/{self.__class__.__name__}: Publishing GNSS position update for vehicle \"{vehicle.vehicle_ref}\" ...")
                            self._iom.publish_gnss_position_update(vehicle_position)

                            self._vehicle_positions[vehicle_position.vehicle.id] = vehicle_position 
                        else:
                            logging.info(f"{self.id}/{self.__class__.__name__}: No actual GNSS position for vehicle \"{vehicle.vehicle_ref}\".")
                    else:
                        logging.info(f"{self.id}/{self.__class__.__name__}: GNSS position for vehicle \"{vehicle.vehicle_ref}\" discarded, vehicle could not be logged on.")

            except Exception as ex:
                logging.error(ex)
            finally:
                
                # wait for the adapter configured timespan until the next request
                time.sleep(self._adapter.interval)

        # shutdown the instance here ...
        for vehicle in (self._vehicles + self._vehicle_blacklist):
            try:
                logging.info(f"{self.id}/{self.__class__.__name__}: Logging off vehicle \"{vehicle.vehicle_ref}\" ...")
                self._iom.log_off_vehicle(vehicle)
            except Exception as ex:
                logging.error(ex)

        self._iom.terminate()