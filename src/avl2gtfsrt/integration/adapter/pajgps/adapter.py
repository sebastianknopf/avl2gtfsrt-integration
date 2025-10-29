import logging
import requests

from datetime import datetime, timedelta
from requests import Response

from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter
from avl2gtfsrt.integration.model.types import VehiclePosition, Vehicle

class PajGpsAdapter(BaseAdapter):
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)

        self._login_token: str|None = None

        self._vehicles: list[Vehicle] = list()
        self._vehicle_expiration: datetime|None = None

    def init(self) -> bool:
        if self._login_expiration is None or self._login_expiration <= datetime.now():
            logging.info(f"{self.instance_id}/{self.__class__.__name__}: Login inactive or expired. Performing login with configured credentials ...")

            login_response: Response = requests.post(
                self._get_url('login'), 
                params={
                    'email': self._username,
                    'password': self._password
                }
            )

            if login_response.status_code != 200:
                return False
            
            # extract and store data for further processing
            login_data: dict = login_response.json()

            self._login_token = login_data['success']['token']
            self._login_expiration = datetime.now() + timedelta(
                seconds=int(login_data['success']['expires_in'])
            )
    
    def get_vehicles(self) -> list[Vehicle]:
        self.init()
        
        if self._vehicle_expiration is None or self._vehicle_expiration <= datetime.now():
            logging.info(f"{self.instance_id}/{self.__class__.__name__}: Vehicle cache expired. Discovering actual vehicles ...")
            
            devices_response: Response = requests.get(
                self._get_url('device'),
                headers={
                    'Authorization': f"Bearer {self._login_token}"
                }
            )

            devices_response.raise_for_status()

            # extract data and store vehicles ...
            devices_data: dict = devices_response.json()
            for device in devices_data['success']:
                self._vehicles.append(Vehicle(
                    id=device['id'],
                    vehicle_ref=device['name']
                ))

            self._vehicle_expiration = datetime.now() + timedelta(
                minutes=30
            )
        else:
            logging.info(f"{self.instance_id}/{self.__class__.__name__}: Vehicles already loaded within the last 30 minutes. Returning cached vehicles ...")

        # return internal loaded vehicle data
        return self._vehicles
    
    def get_vehicle_positions(self) -> list[VehiclePosition]:
        self.init()
        
        logging.info(f"{self.instance_id}/{self.__class__.__name__}: Loading current vehicle positions ...")

        all_last_positions_response: Response = requests.post(
            self._get_url('trackerdata/getalllastpositions'),
            headers={
                'Authorization': f"Bearer {self._login_token}"
            },
            json={
                'deviceIDs': [int(v.id) for v in self._vehicles],
                'fromLastPoint': False
            }
        )

        all_last_positions_response.raise_for_status()

        # extract data and return positions per vehicle
        all_last_positions_data: dict = all_last_positions_response.json()

        positions: list[VehiclePosition] = list()
        for position_data in all_last_positions_data['success']:
            vehicle: Vehicle|None = next((v for v in self._vehicles if int(v.id) == position_data['iddevice']), None)
            if vehicle is not None:
                position: VehiclePosition = VehiclePosition(
                    vehicle=vehicle,
                    latitude=position_data['lat'],
                    longitude=position_data['lng']
                )

                positions.append(position)

        return positions