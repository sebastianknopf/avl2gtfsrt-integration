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
        if self.on_vehicle_log_off is not None:
            self.on_vehicle_log_off(None)
        
        logging.debug(f"{self.instance_id}/{self.__class__.__name__}: Received message: {message}")

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
                self._get_url('socket').replace('https', 'wss'),
                header={
                    'Cookie': f"JSESSIONID={self._login_token}"
                },
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            def _delete_flag(event: Event, ws: WebSocketApp) -> None:
                while event.is_set():
                    time.sleep(1)

                logging.info(f"{self.instance_id}/{self.__class__.__name__}: Stopping WebSocket connection ...")
                self._ws.close()

            delete_thread: Thread = Thread(target=_delete_flag, args=(event, self._ws), daemon=True)
            delete_thread.start()

            # deactivate websocket's internal logger and start connection
            logging.getLogger('websocket').setLevel(logging.CRITICAL)
            self._ws.run_forever()
