from abc import ABC, abstractmethod
from datetime import datetime

from avl2gtfsrt.integration.model.types import Vehicle

class BaseAdapter(ABC):

    def __init__(self, instance_id: str, config: dict) -> None:
        self.instance_id: str = instance_id
        self.endpoint: str = config['endpoint']
        self.autologoff: int = config['autologoff']

        self._username: str|None = config['username']
        self._password: str|None = config['password']

        self._login_token: str|None = None
        self._login_expiration: datetime|None = None

        self._vehicles: list[Vehicle] = list()
    
    def _get_url(self, resource: str) -> str:
        return f"{self.endpoint}/{resource}"
    
    @abstractmethod
    def init(self) -> bool:
        pass