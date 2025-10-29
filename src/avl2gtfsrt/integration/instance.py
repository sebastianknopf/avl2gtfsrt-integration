import logging
import time

from threading import Event, Thread

from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter
from avl2gtfsrt.integration.model.types import Vehicle, VehiclePosition


class AvlDataInstance:

    def __init__(self, config: dict) -> None:
        self.id = config['id']

        # setup everything for the adapter and thread management
        if config['adapter']['type'] == 'pajgps':
            from avl2gtfsrt.integration.adapter.pajgps.adapter import PajGpsAdapter
            self._adapter: BaseAdapter = PajGpsAdapter(config['adapter'])
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
        while self._should_run.is_set():
            # call configured adapter in order to get all current vehicle positions
            logging.info(f"{self.id}/{self.__class__.__name__}: Loading current vehicles ...")
            vehicles_result: list[Vehicle] = self._adapter.get_vehicles()

            # process vehicles here ...

            logging.info(f"{self.id}/{self.__class__.__name__}: Loading current vehicle positions of {len(vehicles_result)} vehicles ...")
            vehicle_positions_result: list[VehiclePosition] = self._adapter.get_vehicle_positions()

            # wait for the adapter configured timespan until the next request
            time.sleep(self._adapter.interval)

        # TODO: implement real shutdown here ...
        logging.info(f"This is the internal shutdown of \"{self.id}\"")