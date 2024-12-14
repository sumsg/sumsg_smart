from dataclasses import dataclass
from .mqtt_client import MqttClient
from homeassistant.util.hass_dict import HassKey # type: ignore
@dataclass
class MQTT_DATA:
  client: MqttClient

MQTT_C: HassKey[MQTT_DATA] = HassKey("mqtt")