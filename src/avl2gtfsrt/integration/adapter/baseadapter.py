from abc import ABC, abstractmethod
from datetime import datetime


class BaseAdapter(ABC):

    def __init__(self, instance_id: str, config: dict) -> None:
        self.instance_id: str = instance_id
        self.endpoint: str = config['endpoint']
        self.autologoff: int = config['autologoff']

        self._username: str|None = config['username']
        self._password: str|None = config['password']
        self._login_expiration: datetime|None = None
    
    @abstractmethod
    def init(self) -> bool:
        pass