import json
import logging
import urllib
import time

from datetime import datetime, timedelta
from requests import Session, Response
from threading import Event, Thread
from websocket import WebSocketApp

from avl2gtfsrt.integration.adapter.realtimeadapter import RealtimeAdapter
from avl2gtfsrt.integration.model.types import VehiclePosition, Vehicle

class TraccarAdapter(RealtimeAdapter):
    
    def __init__(self, instance_id, config: dict):
        super().__init__(instance_id, config)

    def _on_open(self, ws: WebSocketApp) -> None:
        logging.info(f"{self.instance_id}/{self.__class__.__name__}: WebSocket connected.")

    def _on_message(self, ws: WebSocketApp, message: str) -> None:
        data: dict = json.loads(message)

        if 'devices' in data:
            for device in data['devices']:
                device_id: str = device['id']
                vehicle: Vehicle|None = next((v for v in self._vehicles if v.id == device_id), None)

                # add vehicle to tracking if not already present
                if vehicle is None:
                    if 'vehicleId' not in device['attributes']:
                        logging.warning(f"{self.instance_id}/{self.__class__.__name__}: Device {device_id} has no vehicleId attribute. Using name as fallback.")
                    
                    vehicle = Vehicle(
                        id=device_id,
                        vehicle_ref=device['attributes']['vehicleId'] if 'vehicleId' in device['attributes'] else device['name']
                    )

                    self._vehicles.append(vehicle)

        elif 'positions' in data:
            for position in data['positions']:
                device_id: str = position['deviceId']
                vehicle: Vehicle|None = next((v for v in self._vehicles if v.id == device_id), None)

                # ignore position if device / vehicle is not known
                if vehicle is None:
                    logging.warning(f"{self.instance_id}/{self.__class__.__name__}: Received position for unknown device {device_id}. Position was ignored.")
                    continue

                # ignore positon if valid flag is false
                if not position['valid']:
                    logging.info(f"{self.instance_id}/{self.__class__.__name__}: Received invalid position for device {device_id}. Position was ignored.")
                    continue

                vehicle_position: VehiclePosition = VehiclePosition(
                    vehicle=vehicle,
                    latitude=position['latitude'],
                    longitude=position['longitude'],
                    timestamp=int(datetime.fromisoformat(position['fixTime']).timestamp())
                )

                # check whether the vehicle is already logged on
                # if not, trigger a log on at first
                if not vehicle.is_logged_on:
                    vehicle.is_logged_on = True

                    # trigger the callback function if configured
                    if self.on_vehicle_log_on is not None:
                        self.on_vehicle_log_on(vehicle)

                # trigger the callback function if configured
                if self.on_vehicle_physical_position_update is not None:
                    self.on_vehicle_physical_position_update(vehicle_position)

        elif 'events' in data:
            for event in data['events']:
                event_type: str = event['type']
                device_id: str = event['deviceId']
                
                vehicle: Vehicle|None = next((v for v in self._vehicles if v.id == device_id), None)
                if vehicle is None:
                    logging.warning(f"{self.instance_id}/{self.__class__.__name__}: Received event for unknown device {device_id}. Event was ignored.")
                    continue

                if event_type == 'deviceOnline':
                    if not vehicle.is_logged_on:
                        vehicle.is_logged_on = True

                        # trigger the callback function if configured
                        if self.on_vehicle_log_on is not None:
                            self.on_vehicle_log_on(vehicle)

                elif event_type == 'deviceInactive':
                    vehicle.is_logged_on = False

                    # trigger the callback function if configured
                    if self.on_vehicle_log_off is not None:
                        self.on_vehicle_log_off(vehicle)

    def _on_error(self, ws: WebSocketApp, error: Exception) -> None:
        logging.error(f"{self.instance_id}/{self.__class__.__name__}: WebSocket error {str(error)}")

    def _on_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        logging.info(f"{self.instance_id}/{self.__class__.__name__}: WebSocket closed.")

    def init(self) -> bool:
        if self._login_expiration is None or self._login_expiration <= datetime.now():
            logging.info(f"{self.instance_id}/{self.__class__.__name__}: Login inactive or expired. Performing login with configured credentials ...")

            session: Session = Session()
            login_response: Response = session.post(
                self._get_url('session'), 
                data=urllib.parse.urlencode({
                    'email': self._username,
                    'password': self._password
                }),
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'accept': 'application/json'
                }
            )

            if login_response.status_code != 200:
                return False
            
            cookies: dict = session.cookies.get_dict()

            self._login_token = cookies['JSESSIONID']
            self._login_expiration = datetime.now() + timedelta(days=30)

        return True
    
    def run(self, event: Event) -> None:
        while event.is_set():
            self.init()

            logging.info(f"{self.instance_id}/{self.__class__.__name__}: Starting WebSocket connection for realtime updates ...")
            self._ws: WebSocketApp = WebSocketApp(
                self._get_url('socket').replace('https', 'wss').replace('http', 'ws'),
                header={
                    'Cookie': f"JSESSIONID={self._login_token}"
                },
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            def __stop_event_handler(event: Event, ws: WebSocketApp) -> None:
                while event.is_set():
                    time.sleep(1)

                logging.info(f"{self.instance_id}/{self.__class__.__name__}: Stopping WebSocket connection ...")
                self._ws.close()

            delete_thread: Thread = Thread(target=__stop_event_handler, args=(event, self._ws), daemon=True)
            delete_thread.start()

            # deactivate websocket's internal logger and start connection
            logging.getLogger('websocket').setLevel(logging.CRITICAL)
            self._ws.run_forever()
