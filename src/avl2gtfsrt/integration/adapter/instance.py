import logging
import time

from threading import Event, Thread


class AvlDataInstance:

    def __init__(self, config: dict) -> None:
        self.id = config['id']

        # setup everything for the adapter and thread management
        if config['adapter']['type'] == 'pajgps':
            pass
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
        self._thread.join()

    def _run_internal(self) -> None:
        while self._should_run.is_set():
            logging.info(f"Instance \"{self.id}\" is running ...")
            time.sleep(1)

        logging.info(f"This is the internal shutdown of \"{self.id}\"")