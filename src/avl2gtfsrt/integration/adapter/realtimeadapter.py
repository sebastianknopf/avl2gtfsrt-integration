from abc import abstractmethod

from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter

class RealtimeAdapter(BaseAdapter):
    
    def __init__(self, instance_id: str, config: dict) -> None:
        super().__init__(instance_id, config)

        self.on_vehicle_log_on: callable|None = None
        self.on_vehicle_log_off: callable|None = None
        self.on_vehicle_physical_position_update: callable|None = None

    @abstractmethod
    def run(self) -> None:
        pass