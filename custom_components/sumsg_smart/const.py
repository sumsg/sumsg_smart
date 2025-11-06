"""Constants for the Sengled Integration."""
MANUFACTURER = "SUMSG Inc."
DEFAULT_NAME = "Sumsg Smart"
DOMAIN = "sumsg_smart"

MQTT_HOST = "broker.iot.sumsg.com"
MQTT_PORT = 1315

CONF_USER_NAME = "username"
CONF_PASSWORD = "password"

CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_IP = "device_ip"
CONF_WIFI_PASSWORD = "wifi_password"

DEVICE_TYPE_LAN = "lan"
DEVICE_TYPE_CLOUD = "cloud"

DEVICE_TYPES = {
    DEVICE_TYPE_LAN: "局域网版本",
    DEVICE_TYPE_CLOUD: "网络版本"
}