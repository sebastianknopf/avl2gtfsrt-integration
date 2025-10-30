import logging

from datetime import datetime, timezone
from paho.mqtt import client as mqtt

from avl2gtfsrt.integration.model.types import Vehicle, VehiclePosition
from avl2gtfsrt.integration.vdv.vdv435 import VehicleRef, TechnicalVehicleLogOnRequestStructure, TechnicalVehicleLogOffRequestStructure, GnssPhysicalPositionDataStructure, GnssPhysicalPosition, WGS84PhysicalPosition

class TopicLevelStructureDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"

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

        # create TLS topic structures
        self._tls_pub_itcs_inbox: tuple[str, int] = ("IoM/1.0/DataVersion/any/Inbox/ItcsInbox/Country/de/any/Organisation/{organisation_id}/any/ItcsId/{itcs_id}/RequestData", 2)
        self._tls_pub_vehicle_physical_position: tuple[str, int] = ("IoM/1.0/DataVersion/any/Country/de/any/Organisation/{organisation_id}/any/Vehicle/{vehicle_ref}/any/PhysicalPosition/GnssPhysicalPositionData", 0)

        # keep track of all global placeholders here
        # used in _get_tls method later
        self._tls_dict: TopicLevelStructureDict = TopicLevelStructureDict()
        self._tls_dict['organisation_id'] = self.organisation_id
        self._tls_dict['itcs_id'] = self.itcs_id

        # set MQTT parameters
        self._mqtt_host: str = config['host']
        self._mqtt_port: str = config['port']
        self._mqtt_username: str = config['username']
        self._mqtt_password: str = config['password']        

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc.is_failure:
            raise RuntimeError("Failed to connect to the IoM MQTT broker.")

    def _on_message(self, client, userdata, message):
        logging.info(f"{self.__class__.__name__}: Received message in topic {message.topic}")

    def _on_disconnect(self, client, userdata, flags, rc, properties):
        pass

    def _get_tls(self, tls_name: str) -> tuple[str, int]:
        if not tls_name.startswith('_tls_'):
            tls_name = f"_tls_{tls_name}"

        tls: tuple = getattr(self, tls_name, None)
        if tls is not None and isinstance(tls, tuple):
            tls_str: str = tls[0]
            tls_str = tls_str.format_map(self._tls_dict)

            return (tls_str, tls[1])
        else:
            raise ValueError(f"Undefined TLS {tls_name} not found!")
        
    def _publish(self, tls_name: str, payload: str, retain=False, **arguments):
        tls: tuple[str, int] = self._get_tls(tls_name)

        tls_str: str = tls[0]
        tls_str = tls_str.format(**arguments)

        self._mqtt.publish(
            tls_str,
            payload,
            tls[1],
            retain
        )

        logging.info(f"{self.__class__.__name__}: Published message to topic {tls_str}")
    
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
        vehicle_ref: VehicleRef = VehicleRef(**{'#text': vehicle.vehicle_ref})
        
        log_on_message: TechnicalVehicleLogOnRequestStructure = TechnicalVehicleLogOnRequestStructure(**{
            'netex:VehicleRef': vehicle_ref
        })

        self._publish('pub_itcs_inbox', log_on_message.xml())

    def log_off_vehicle(self, vehicle: Vehicle) -> bool:
        vehicle_ref: VehicleRef = VehicleRef(**{'#text': vehicle.vehicle_ref})
        
        log_off_message: TechnicalVehicleLogOffRequestStructure = TechnicalVehicleLogOffRequestStructure(**{
            'netex:VehicleRef': vehicle_ref
        })

        self._publish('pub_itcs_inbox', log_off_message.xml())

    def publish_gnss_position_update(self, vehicle_position: VehiclePosition) -> None:
        dt: datetime = datetime.fromtimestamp(vehicle_position.timestamp, tz=timezone.utc)
        timestamp_of_measurement: str = dt.replace(microsecond=0).isoformat()
        
        gnss_physical_position_structure: GnssPhysicalPositionDataStructure = GnssPhysicalPositionDataStructure(
            PublisherId=self._mqtt._client_id,
            TimestampOfMeasurement=timestamp_of_measurement,
            GnssPhysicalPosition=GnssPhysicalPosition(
                WGS84PhysicalPosition=WGS84PhysicalPosition(
                    Latitude=vehicle_position.latitude,
                    Longitude=vehicle_position.longitude
                )
            )
        )

        self._publish(
            'pub_vehicle_physical_position', 
            gnss_physical_position_structure.xml(), 
            {
                'vehicle_ref': vehicle_position.vehicle.vehicle_ref
            }
        )