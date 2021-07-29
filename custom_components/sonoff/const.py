from datetime import timedelta

TEMP_CELSIUS = "°C"
DOMAIN = "sonoff"
EWELINK_API = "ewelink_api"
CONF_API_REGION = "api_region"
CONF_GRACE_PERIOD = "grace_period"
SCAN_INTERVAL = timedelta(seconds=1)
CONF_DEBUG = "debug"
CONF_ENTITY_PREFIX = "entity_prefix"

SONOFF_SENSORS_MAP = {
    "power": {"device_class": "power", "uom": "W", "icon": "mdi:flash-outline"},
    "current": {"device_class": "current", "uom": "A", "icon": "mdi:current-ac"},
    "voltage": {"device_class": "voltage", "uom": "V", "icon": "mdi:power-plug"},
    # "dusty": {"device_class": "dusty", "uom": "µg/m3", "icon": "mdi:select-inverse"},
    "light": {"device_class": "light", "uom": "lx", "icon": "mdi:car-parking-lights"},
    # "noise": {"device_class": "noise", "uom": "Db", "icon": "mdi:surround-sound"},
    "currentHumidity": {
        "device_class": "humidity",
        "uom": "%",
        "icon": "mdi:water-percent",
    },
    "humidity": {"device_class": "humidity", "uom": "%", "icon": "mdi:water-percent"},
    "currentTemperature": {
        "device_class": "temperature",
        "uom": TEMP_CELSIUS,
        "icon": "mdi:thermometer",
    },
    "temperature": {
        "device_class": "temperature",
        "uom": TEMP_CELSIUS,
        "icon": "mdi:thermometer",
    },
}
