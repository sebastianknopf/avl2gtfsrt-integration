import logging

from paho.mqtt import client as mqtt

from avl2gtfsrt.integration.model.types import Vehicle, VehiclePosition


class IomClient:

    def __init__(self, instance_id: str,  organisation_id: str, itcs_id: str, config: dict) -> None:
        self.instance_id: str = instance_id
        self.organisation_id: str = organisation_id
        self.itcs_id: str = itcs_id

        # create MQTT client
        self._mqtt: mqtt.Client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, 
            protocol=mqtt.MQTTv5, 
            client_id=f"avl2gtfsrt-integration-IoM-{self.organisation_id}"
        )

        # set MQTT parameters
        self._mqtt_host: str = config['host']
        self._mqtt_port: str = config['port']
        self._mqtt_username: str = config['username']
        self._mqtt_password: str = config['password']        

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc.is_failure:
            raise RuntimeError("Failed to connect to the IoM MQTT broker!")

    def _on_message(self, client, userdata, message):
        pass

    def _on_disconnect(self, client, userdata, flags, rc, properties):
        pass

    def start(self) -> None:
        # define MQTT callback methods
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_message = self._on_message
        self._mqtt.on_disconnect = self._on_disconnect

        # set username and password if provided
        if self._mqtt_username is not None and self._mqtt_password is not None:
            self._mqtt.username_pw_set(username=self._mqtt_username, password=self._mqtt_password)

        # finally connect to the broker ...
        logging.info(f"{self.instance_id}/{self.__class__.__name__}: Connecting to MQTT broker at {self._mqtt_host}:{self._mqtt_port} ...")
        self._mqtt.connect(self._mqtt_host, int(self._mqtt_port))
        
        self._mqtt.loop_start()

    def terminate(self) -> None:
        logging.info(f"{self.instance_id}/{self.__class__.__name__}: Shutting down MQTT connection ...")
        self._mqtt.disconnect()

        self._mqtt.loop_stop()
    
    def log_on_vehicle(self, vehicle: Vehicle) -> bool:
        pass

    def log_off_vehicle(self, vehicle: Vehicle) -> bool:
        pass

    def publish_gnss_position_update(self, vehicle_position: VehiclePosition) -> None:
        pass