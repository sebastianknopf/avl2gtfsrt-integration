from threading import Event

from avl2gtfsrt.integration.iom.client import IomClient
from avl2gtfsrt.integration.adapter.realtimeadapter import RealtimeAdapter

class TraccarAdapter(RealtimeAdapter):
    
    def __init__(self, instance_id, config, iom: IomClient):
        super().__init__(instance_id, config, iom)

    def init(self) -> bool:
        return True
    
    def run(self, event: Event) -> None:
        while event.is_set():
            pass