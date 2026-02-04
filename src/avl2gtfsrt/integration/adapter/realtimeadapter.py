from abc import abstractmethod

from avl2gtfsrt.integration.iom.client import IomClient
from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter

class RealtimeAdapter(BaseAdapter):
    
    def __init__(self, instance_id: str, config: dict, iom: IomClient) -> None:
        super().__init__(instance_id, config)

        self._iom: IomClient = iom

    @abstractmethod
    def run(self) -> None:
        pass