import yaml

from avl2gtfsrt.integration.config import Configuration

class InstanceManager():
    
    def __init__(self, config_filename: str) -> None:
        
        # load config and set default values
        with open(config_filename, 'r') as config_file:
            self._config = yaml.safe_load(config_file)

        self._config: dict = Configuration.default_config(self._config)

        # start a thread for each configured instance
        for instance in self._config['instance']:
            pass

    def run(self) -> None:
        pass