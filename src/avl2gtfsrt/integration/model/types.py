from dataclasses import dataclass, field

@dataclass
class Vehicle:
    id: any
    vehicle_ref: str

@dataclass
class VehiclePosition:
    vehicle: Vehicle
    latitude: float
    longitude: float