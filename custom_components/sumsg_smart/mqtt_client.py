import json
import logging
import ssl
from .const import DOMAIN, MQTT_HOST,MQTT_PORT
import paho.mqtt.client as mqtt # type: ignore
from homeassistant.core import HomeAssistant # type: ignore

TLS_CONTEXT = ssl.create_default_context()
TLS_CONTEXT.check_hostname = False
TLS_CONTEXT.verify_mode = ssl.CERT_NONE

_LOGGER = logging.getLogger(__name__)

class MqttClient:
    """MqttClient controller."""
    def __init__(
        self,
        hass: HomeAssistant,
        username,
        password,
        devices,
    ):
        """Initialize configured controller."""
        self._hass = hass
        self._username = username
        self._password = password
        self._mqtt = None
        self._devices = {}
        self._devicesEntity = {}
        for device in devices:
            product_name = device.get('productName')
            if product_name == 'pcSw3' or product_name == 'pcSw1' or product_name == 'powerSwitch1' or product_name == 'pcHealth1':
                device_id = device.get('token')
                self._devices[device_id] = device
    async def connect(self):
        _LOGGER.info("Start connecting to cloud MQTT-server")
        def on_connect_callback(client, userdata, flags, res):
            _LOGGER.info("Connected to MQTT")
            try:
                if self._mqtt.is_connected():
                    for device_id, device in self._devices.items():
                        model = device.get('productName')
                        topic = f"su/{model}/{device_id}/server"
                        self._mqtt.subscribe(topic)
            except Exception as exc: 
                logging.exception(exc)
        def on_disconnect_callback(client, userdata, rc):
            _LOGGER.info(f"Disconnected from MQTT")
            self._mqtt.reconnect()
        def on_subscribe_callback(client, userdata, mid, granted_qos):
            for unique_id, device_entity in self._devicesEntity.items():
                device_entity.sync_system_data()
        def on_message_callback(client, userdata, message):
            try:
                self._mqtt_process_message(message)
            except Exception as exc:
                logging.exception(exc)
        self._mqtt = mqtt.Client(
            client_id=  f"hass_{self._username}",
            clean_session=True,
            reconnect_on_failure=True,
        )
        self._mqtt.enable_logger(_LOGGER)
        self._mqtt.on_connect = on_connect_callback
        self._mqtt.on_message = on_message_callback
        self._mqtt.on_disconnect = on_disconnect_callback
        self._mqtt.on_subscribe = on_subscribe_callback
        self._mqtt.username_pw_set(self._username, self._password)
        self._mqtt.tls_set_context(context=TLS_CONTEXT)
        # self._mqtt.tls_set(cert_reqs=ssl.CERT_NONE)
        # self._mqtt.tls_insecure_set(True)
        self._mqtt.connect_async(
            host=MQTT_HOST, 
            port=MQTT_PORT,
        )
        self._mqtt.loop_start()
    def entities_append(self,entity_id,entity):
        self._devicesEntity[entity_id] = entity
    def clear_entities(self):
        self._devicesEntity = {}
    def _mqtt_process_message(self, message: dict):
        if not self._devicesEntity:
            return
        # _LOGGER.info(f"message:{message.payload}")
        legacy_topic = message.topic.split("/")
        model = legacy_topic[1]
        device_id = legacy_topic[2]
        payload = json.loads(message.payload)
        if model=="pcSw3" or model=="pcSw1":
            for control_id in [0,2,3,4,5,6]:
                entity_id = f"{DOMAIN}_{control_id}_{device_id}"
                devicesEntity = self._devicesEntity.get(entity_id)
                if devicesEntity:
                    devicesEntity.set_system_data(device_id,control_id,model,payload)
        if model=="powerSwitch1":
            control_id = 0
            entity_id = f"{DOMAIN}_{control_id}_{device_id}"
            devicesEntity = self._devicesEntity.get(entity_id)
            if devicesEntity:
                devicesEntity.set_system_data(device_id,control_id,model,payload)
    #
    def publish(self,topic,payload):
        if not self._mqtt.is_connected():
            return
        self._mqtt.publish(topic, json.dumps(payload), qos=1)
    def disconnect(self):
        self._mqtt.disconnect()
    @property
    def client(self) -> mqtt:
        return self._mqtt