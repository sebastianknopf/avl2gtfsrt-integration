from avl2gtfsrt.integration.model.types import Vehicle, VehiclePosition


class IomClient:

    def __init__(self, organisation_id: str, itcs_id: str, config: dict) -> None:
        self.organisation_id = config['organisation']
        self.itcs_id = itcs_id

    def start(self) -> None:
        pass

    def terminate(self) -> None:
        pass
    
    def log_on_vehicle(vehicle: Vehicle) -> bool:
        pass

    def log_off_vehicle(vehicle: Vehicle) -> bool:
        pass

    def publish_gnss_position_update(vehicle_position: VehiclePosition) -> None:
        pass