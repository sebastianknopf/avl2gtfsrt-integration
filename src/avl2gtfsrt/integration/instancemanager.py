import logging
import signal
import time
import yaml

from threading import Event

from avl2gtfsrt.integration.instance import AvlDataInstance
from avl2gtfsrt.integration.config import Configuration

class InstanceManager():
    
    def __init__(self, config_filename: str) -> None:
        # load config and set default values
        with open(config_filename, 'r') as config_file:
            self._config = yaml.safe_load(config_file)

        self._config: dict = Configuration.default_config(self._config)

        # keep track of all instance threads
        self._instances: list[AvlDataInstance] = list()

        # start a thread for each configured instance
        for i in self._config['instances']:
            logging.info(f"{self.__class__.__name__}: Creating instance \"{i['id']}\" ...")

            instance: AvlDataInstance = AvlDataInstance(i)
            instance.run()

            self._instances.append(instance)

        # keep track of stopping flag
        self._should_run = Event()
        self._should_run.set()

    def run(self) -> None:
        # register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while self._should_run.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.stop()

    def stop(self) -> None:
        for instance in self._instances:
            logging.info(f"{self.__class__.__name__}: Shutting down instance \"{instance.id}\" ...")
            
            instance.stop()
    
    def _signal_handler(self, signum, frame):
        logging.info(f'{self.__class__.__name__}: Received signal {signum}')
        self._should_run.clear()
        