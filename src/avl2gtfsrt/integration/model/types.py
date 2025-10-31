from dataclasses import dataclass, field

@dataclass
class Vehicle:
    id: any
    vehicle_ref: str
    is_logged_on: bool = False

@dataclass
class VehiclePosition:
    vehicle: Vehicle
    latitude: float
    longitude: float
    timestamp: int