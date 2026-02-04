from abc import abstractmethod

from avl2gtfsrt.integration.model.types import VehiclePosition, Vehicle
from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter


class PollingAdapter(BaseAdapter):

    def __init__(self, instance_id: str, config: dict) -> None:
        super().__init__(instance_id, config)

        self.interval: int = config['interval']

    @abstractmethod
    def get_vehicles(self) -> list[Vehicle]:
        pass

    @abstractmethod
    def get_vehicle_positions(self) -> list[VehiclePosition]:
        pass