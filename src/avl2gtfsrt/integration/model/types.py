from dataclasses import dataclass, field

@dataclass
class Vehicle:
    id: any
    vehicle_ref: str
    is_logged_on: bool = False

    def __eq__(self, value):
        if isinstance(value, Vehicle):
            return self.id == value.id
        else:
            return False

@dataclass
class VehiclePosition:
    vehicle: Vehicle
    latitude: float
    longitude: float
    timestamp: int

    def __eq__(self, value):
        if isinstance(value, VehiclePosition):
            return self.vehicle == value.vehicle and self.timestamp == value.timestamp
        else:
            return False