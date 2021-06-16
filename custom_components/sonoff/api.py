import base64
import hashlib
import hmac
import json
import logging
import random
import re
import string
import threading
import time
from typing import Dict, List

import aiohttp
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    HTTP_BAD_REQUEST,
    HTTP_MOVED_PERMANENTLY,
    HTTP_NOT_FOUND,
    HTTP_UNAUTHORIZED,
)
import websocket

from .const import SONOFF_SENSORS_MAP

APP_ID = "YzfeftUVcZ6twZw1OoVKPRFYTrGEg01Q"
APP_SECRET = b"4G91qSoboqYO4Y0XJ0LPPKIsq8reHdfa"

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

NAME_TO_CHANNEL_MAP = {
    "SOCKET": 1,
    "SWITCH_CHANGE": 1,
    "GSM_UNLIMIT_SOCKET": 1,
    "SWITCH": 1,
    "THERMOSTAT": 1,
    "SOCKET_POWER": 1,
    "GSM_SOCKET": 1,
    "POWER_DETECTION_SOCKET": 1,
    "SOCKET_2": 2,
    "GSM_SOCKET_2": 2,
    "SWITCH_2": 2,
    "SOCKET_3": 3,
    "GSM_SOCKET_3": 3,
    "SWITCH_3": 3,
    "SOCKET_4": 4,
    "GSM_SOCKET_4": 4,
    "SWITCH_4": 4,
    "CUN_YOU_DOOR": 4,
}

UIID_TO_NAME_MAP = {
    1: "SOCKET",
    2: "SOCKET_2",
    3: "SOCKET_3",
    4: "SOCKET_4",
    5: "SOCKET_POWER",
    6: "SWITCH",
    7: "SWITCH_2",
    8: "SWITCH_3",
    9: "SWITCH_4",
    10: "OSPF",
    11: "CURTAIN",
    12: "EW-RE",
    13: "FIREPLACE",
    14: "SWITCH_CHANGE",
    15: "THERMOSTAT",
    16: "COLD_WARM_LED",
    17: "THREE_GEAR_FAN",
    18: "SENSORS_CENTER",
    19: "HUMIDIFIER",
    22: "RGB_BALL_LIGHT",
    23: "NEST_THERMOSTAT",
    24: "GSM_SOCKET",
    25: "AROMATHERAPY",
    26: "RuiMiTeWenKongQi",
    27: "GSM_UNLIMIT_SOCKET",
    28: "RF_BRIDGE",
    29: "GSM_SOCKET_2",
    30: "GSM_SOCKET_3",
    31: "GSM_SOCKET_4",
    32: "POWER_DETECTION_SOCKET",
    33: "LIGHT_BELT",
    34: "FAN_LIGHT",
    35: "EZVIZ_CAMERA",
    36: "SINGLE_CHANNEL_DIMMER_SWITCH",
    38: "HOME_KIT_BRIDGE",
    40: "FUJIN_OPS",
    41: "CUN_YOU_DOOR",
    42: "SMART_BEDSIDE_AND_NEW_RGB_BALL_LIGHT",
    43: "",
    44: "",
    45: "DOWN_CEILING_LIGHT",
    46: "AIR_CLEANER",
    49: "MACHINE_BED",
    51: "COLD_WARM_DESK_LIGHT",
    52: "DOUBLE_COLOR_DEMO_LIGHT",
    53: "ELECTRIC_FAN_WITH_LAMP",
    55: "SWEEPING_ROBOT",
    56: "RGB_BALL_LIGHT_4",
    57: "MONOCHROMATIC_BALL_LIGHT",
    59: "MUSIC_LIGHT_BELT",
    60: "NEW_HUMIDIFIER",
    61: "KAI_WEI_ROUTER",
    62: "MEARICAMERA",
    66: "ZIGBEE_MAIN_DEVICE",
    67: "RollingDoor",
    68: "KOOCHUWAH",
    1001: "BLADELESS_FAN",
    1003: "WARM_AIR_BLOWER",
    1000: "ZIGBEE_SINGLE_SWITCH",
    1770: "ZIGBEE_TEMPERATURE_SENSOR",
    1256: "ZIGBEE_LIGHT",
}


def map_to_devices(device):
    devices = []
    for sensor in SONOFF_SENSORS_MAP.keys():
        if (
            device["params"].get(sensor)
            and device["params"].get(sensor) != "unavailable"
        ):
            entity = SonoffDevice(
                device["deviceid"], device["name"], device["online"], sensor
            )
            devices.append(entity)
    if "switch" in device["params"]:
        entity = SonoffDevice(
            device["deviceid"], device["name"], device["online"], sensor
        )
        devices.append(entity)


class SonoffDevice:
    device_id: str
    name: str
    available: bool
    mac: str
    model: str
    firmware_version: str
    channels: int
    switches: List[bool]

    def __init__(self, data: Dict) -> None:
        uiid = data.get("uiid")
        self.device_id = data.get("deviceid")
        self.name = data.get("name")
        self.available = data.get("online")
        self.mac = data.get("extra", {}).get("extra", {}).get("mac")
        self.model = data.get("extra", {}).get("extra", {}).get("model")

        params = data.get("params", {})

        def get_param(name, converter):
            value = params.get(name)
            if value and value != "unavailable":
                return converter(value)

        self.firmware_version = get_param("fwVersion", str)
        self.power = get_param("power", float)
        self.current = get_param("current", float)
        self.voltage = get_param("voltage", float)
        self.dusty = get_param("dusty", float)
        self.light = get_param("light", float)
        self.noise = get_param("noise", float)
        # TH10/TH16
        self.humidity = get_param("currentHumidity", float)
        self.temperature = get_param("currentTemperature", float)

        self.humidity = get_param("humidity", float)
        self.temperature = get_param("temperature", float)
        self.rssi = get_param("rssi", float)

        def switch_to_bool(state):
            return state == "on"

        if "switch" in params:  # the device has one switch
            self.switches = [get_param("switch", switch_to_bool)]

        if "switches" in params:  # the device has more switches
            self.switches = [switch_to_bool(sw) for sw in params.get("switches")]

        if (
            uiid in UIID_TO_NAME_MAP.keys()
            and UIID_TO_NAME_MAP[uiid] in NAME_TO_CHANNEL_MAP.keys()
        ):
            self.channels = NAME_TO_CHANNEL_MAP[UIID_TO_NAME_MAP[uiid]]

    def __repr__(self) -> str:
        states = ", ".join(["on" if switch else "off" for switch in self.switches])
        return f"[{self.device_id}] {self.name} {states}"


def timestamp():
    return str(int(time.time()))


def sequence():
    return str(time.time()).replace(".", "")


def credentialsPayload(username, password) -> dict:
    payload = {
        "appid": APP_ID,  # "oeVkj2lYFGnJu5XUtWisfW4utiN4u9Mq",
        "password": password,
        "ts": timestamp(),
        "version": "8",
        "nonce": "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
        ),
    }
    if re.match(r"[^@]+@[^@]+\.[^@]+", username):
        payload["email"] = username
    else:
        payload["phoneNumber"] = username
    return payload


def wssLoginPayload(at, api_key) -> dict:
    return {
        "action": "userOnline",
        "at": at,
        "apikey": api_key,
        "appid": APP_ID,
        "nonce": "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
        ),
        "ts": timestamp(),
        "userAgent": "app",
        "sequence": sequence(),
        "version": 8,
    }


def wssUpdatePayload(api_key, device_id, params) -> dict:
    return {
        "action": "update",
        "apikey": api_key,
        "deviceid": device_id,
        "selfApikey": api_key,
        "params": params,
        "ts": timestamp(),
        "userAgent": "app",
        "sequence": sequence(),
    }


class EWeLinkApi:
    def __init__(self, username, password, region):
        self._username = username
        self._password = password
        self._api_region = region
        self._devices = []
        self._wshost = None
        self._ws = None

        self._skipped_login = 0
        self._grace_period = 600
        self._scan_interval = 10

    def device(self, device_id: str) -> SonoffDevice:
        for device in self.devices:
            if device.device_id == device_id:
                return device

    async def do_login(self, session: aiohttp.ClientSession):
        import uuid

        # reset the grace period
        self._skipped_login = 0
        self._imei = str(uuid.uuid4())

        _LOGGER.debug(
            json.dumps(
                {
                    "imei": self._imei,
                }
            )
        )

        app_details = credentialsPayload(self._username, self._password)

        decryptedAppSecret = APP_SECRET  # b"6Nz4n0xA8s8qdxQf2GqurZj2Fs55FUvM"

        hex_dig = hmac.new(
            decryptedAppSecret,
            str.encode(json.dumps(app_details)),
            digestmod=hashlib.sha256,
        ).digest()

        sign = base64.b64encode(hex_dig).decode()

        self._headers = {
            "Authorization": "Sign " + sign,
            "Content-Type": "application/json;charset=UTF-8",
        }

        r = await session.post(
            f"https://{self._api_region}-api.coolkit.cc:8080/api/user/login",
            headers=self._headers,
            json=app_details,
        )

        resp = await r.json()
        # get a new region to login
        if (
            "error" in resp
            and "region" in resp
            and resp["error"] == HTTP_MOVED_PERMANENTLY
        ):
            self._api_region = resp["region"]
            self._wshost = None

            _LOGGER.warning(
                "found new region: >>> %s <<< (you should change api_region option to this value in integrations)",
                self._api_region,
            )

            # re-login using the new localized endpoint
            await self.do_login(session)

        elif "error" in resp and resp["error"] in [HTTP_NOT_FOUND, HTTP_BAD_REQUEST]:
            # (most likely) login with +86... phone number and region != cn
            if "@" not in self._username and self._api_region in ["eu", "us"]:
                _LOGGER.error(
                    "Login failed! try to change the api_region to 'cn' OR 'as'"
                )

            else:
                _LOGGER.error("Couldn't authenticate using the provided credentials!")

        else:
            if "at" not in resp:
                _LOGGER.error("Login failed! Please check credentials!")
                return

            self._bearer_token = resp["at"]
            self._user_apikey = resp["user"]["apikey"]
            self._headers.update({"Authorization": "Bearer " + self._bearer_token})

            await self.update_devices(session)  # to write the devices list

            if not self._wshost:
                await self.set_wshost(session)

            if self._wshost is not None:
                self.thread = threading.Thread(target=self.init_websocket)
                self.thread.daemon = True
                self.thread.start()

    async def set_wshost(self, session: aiohttp.ClientSession):
        r = await session.post(
            f"https://{self._api_region}-disp.coolkit.cc:8080/dispatch/app",
            headers=self._headers,
        )
        resp = await r.json()
        if "error" in resp and resp["error"] == 0 and "domain" in resp:
            self._wshost = resp["domain"]
            _LOGGER.info("Found websocket address: %s", self._wshost)
        else:
            _LOGGER.error("Couldn't find a valid websocket host, aborting Sonoff init")

    def init_websocket(self):
        # keep websocket open indefinitely
        while True:
            _LOGGER.debug("(re)init websocket")
            self._ws = EWeLinkApiWebsocketListener(
                wshost=self._wshost,
                bearer_token=self._bearer_token,
                api_key=self._user_apikey,
                on_message=self.on_message,
                on_error=self.on_error,
            )

            try:
                # 145 interval is defined by the first websocket response after login
                self._ws.run_forever(ping_interval=145)
            finally:
                self._ws.close()

    def on_message(self, *args):
        data = args[
            -1
        ]  # to accomodate the weird behaviour where the function receives 2 or 3 args
        data = json.loads(data)
        _LOGGER.warning(data)
        if "error" in data and data["error"] > 0:
            _LOGGER.error("Skipping websocket processing")
            _LOGGER.error(data)
            return

        device_id = data.get("deviceid")
        if device_id:
            device = self.device(device_id)
        if "action" in data and data["action"] == "update" and "params" in data:
            params = data["params"]
            if device is None:
                _LOGGER.error(f"{device_id} is not found in the state")
                return

            if "switch" in params:
                device.switches[0] = True if params["switch"] == "on" else False
            if "power" in params:
                device.power = float(params["power"])
            if "voltage" in params:
                device.voltage = float(params["voltage"])
            if "current" in params:
                device.current = float(params["current"])

        if "action" in data and data["action"] == "sysmsg" and "params" in data:
            params = data["params"]
            device_id = data["deviceid"]
            if device is None:
                _LOGGER.error(f"{device_id} is not found in the state")
                return
            if "online" in params:
                device.available = params["online"]

    def on_error(self, *args):
        error = args[-1]
        _LOGGER.error(f"websocket error: {error}")

    async def update_devices(self, session):
        if self._user_apikey is None:
            _LOGGER.error("Initial login failed, devices cannot be updated!")
            return self._devices

        # we are in the grace period, no updates to the devices
        if self._skipped_login and self.is_grace_period():
            _LOGGER.info("Grace period active")
            return self._devices

        r = await session.get(
            "https://{}-api.coolkit.cc:8080/api/user/device?lang=en&apiKey={}&getTags=1&version=6&ts=%s&nonce=%s&appid=oeVkj2lYFGnJu5XUtWisfW4utiN4u9Mq&imei=%s".format(
                self._api_region,
                self._user_apikey,
                str(int(time.time())),
                "".join(
                    random.choice(string.ascii_lowercase + string.digits)
                    for _ in range(8)
                ),
                self._imei,
            ),
            headers=self._headers,
        )

        resp = await r.json()
        if "error" in resp and resp["error"] in [HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED]:
            if self.is_grace_period():
                _LOGGER.warning("Grace period activated!")
                return

            _LOGGER.info("Re-login component")
            await self.do_login(session)

        device_data_list = resp["devicelist"] if "devicelist" in resp else resp
        self.devices = [SonoffDevice(device_data) for device_data in device_data_list]

    def switch(self, device_id, outlet, state):
        device = self.device(device_id)

        def bool_to_state(b):
            if b:
                return "on"
            else:
                return "off"

        if device.channels == 1:
            params = {"switch": bool_to_state(state)}
        else:
            params = {"switches": [bool_to_state(switch) for switch in device.switches]}
            params["switches"][outlet] = bool_to_state(state)

        payload = wssUpdatePayload(self._user_apikey, device_id, params)
        self._ws.send(json.dumps(payload))
        self.device(device_id).switches[outlet] = state

    def is_grace_period(self):
        grace_time_elapsed = self._skipped_login * self._scan_interval
        grace_status = grace_time_elapsed < self._grace_period
        _LOGGER.info(f"GRACE {grace_status}")
        if grace_status:
            self._skipped_login += 1

        return grace_status


class EWeLinkApiWebsocketListener(threading.Thread, websocket.WebSocketApp):
    def __init__(
        self,
        wshost,
        bearer_token,
        api_key,
        on_message=None,
        on_error=None,
    ):
        threading.Thread.__init__(self)
        websocket.WebSocketApp.__init__(
            self,
            "wss://{}:8080/api/ws".format(wshost),
            on_open=self.on_open,
            on_error=on_error,
            on_message=on_message,
            on_close=self.on_close,
        )
        self._bearer_token = bearer_token
        self._api_key = api_key
        self.connected = False
        self.last_update = time.time()

    def on_open(self, *args):
        self.connected = True
        self.last_update = time.time()

        payload = wssLoginPayload(self._bearer_token, self._api_key)

        self.send(json.dumps(payload))

    def on_close(self, *args):
        _LOGGER.debug("websocket closed")
        self.connected = False

    def run_forever(
        self, sockopt=None, sslopt=None, ping_interval=0, ping_timeout=None
    ):
        websocket.WebSocketApp.run_forever(
            self,
            sockopt=sockopt,
            sslopt=sslopt,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
        )


async def main():
    son = EWeLinkApi()
    async with aiohttp.ClientSession() as client:
        await son.do_login(client)
        time.sleep(20)
        son.switch("10010d48f9", False)
        time.sleep(500)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
