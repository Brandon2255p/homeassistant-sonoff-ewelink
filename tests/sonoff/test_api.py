import unittest

from custom_components.sonoff.api import SonoffDevice


class TestSonoffDevice(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)

    def test_sonoff_basic(self):
        data = {
            "settings": {
                "opsNotify": 0,
                "opsHistory": 1,
                "alarmNotify": 1,
                "wxAlarmNotify": 0,
                "wxOpsNotify": 0,
                "wxDoorbellNotify": 0,
                "appDoorbellNotify": 1,
            },
            "family": {"id": "60c88756cba1160008758085", "index": 0},
            "group": "",
            "online": True,
            "shareUsersInfo": [],
            "groups": [],
            "devGroups": [],
            "relational": [],
            "deviceid": "10010d48f9",
            "name": "Heater",
            "type": "10",
            "params": {
                "version": 8,
                "only_device": {"ota": "success"},
                "sledOnline": "on",
                "ssid": "Aruba",
                "bssid": "00:00:00:00:00:00",
                "switch": "on",
                "fwVersion": "3.5.1",
                "rssi": -70,
                "staMac": "C4:DD:57:2E:31:F6",
                "startup": "off",
                "init": 1,
                "pulse": "off",
                "pulseWidth": 500,
            },
            "createdAt": "2021-06-15T11:10:33.529Z",
            "__v": 0,
            "onlineTime": "2021-06-16T17:18:05.312Z",
            "ip": "41.157.217.252",
            "location": "",
            "tags": {"m_5378_bran": "on"},
            "offlineTime": "2021-06-15T11:13:10.724Z",
            "sharedTo": [],
            "devicekey": "99b04800-4f5d-44bf-a9dd-e80c6829a345",
            "deviceUrl": "https://eu-api.coolkit.cc/api/detail/5c700f76cc248c47441fd234_en.html",
            "brandName": "SONOFF",
            "showBrand": True,
            "brandLogoUrl": "https://eu-ota.coolkit.cc/logo/q62PevoglDNmwUJ9oPE7kRrpt1nL1CoA.png",
            "productModel": "BASIC",
            "devConfig": {},
            "uiid": 1,
        }
        device = SonoffDevice(data)
        self.assertEqual(device.name, "Heater")
        self.assertEqual(device.device_id, "10010d48f9")
        self.assertEqual(device.channels, 1)
        self.assertEqual(device.available, True)
        self.assertEqual(device.switches, [True])
        self.assertEqual(str(device), "[10010d48f9] Heater on")

    def test_sonoff_basic_off(self):
        data = {
            "online": True,
            "deviceid": "10010d48f9",
            "name": "Heater",
            "params": {
                "switch": "off",
            },
            "uiid": 1,
        }
        device = SonoffDevice(data)
        self.assertEqual(device.name, "Heater")
        self.assertEqual(device.device_id, "10010d48f9")
        self.assertEqual(device.channels, 1)
        self.assertEqual(device.available, True)
        self.assertEqual(device.switches, [False])
        self.assertIsNone(device.power)
        self.assertEqual(str(device), "[10010d48f9] Heater off")

    def test_sonoff_socket_two(self):
        data = {
            "online": True,
            "deviceid": "10010d48f9",
            "name": "Heater",
            "params": {
                "switches": ["off", "on"],
            },
            "uiid": 2,
        }
        device = SonoffDevice(data)
        self.assertEqual(device.name, "Heater")
        self.assertEqual(device.device_id, "10010d48f9")
        self.assertEqual(device.channels, 2)
        self.assertEqual(device.available, True)
        self.assertEqual(device.switches, [False, True])
        self.assertIsNone(device.power)
        self.assertEqual(str(device), "[10010d48f9] Heater off, on")

    def test_sonoff_power_2(self):
        data = {
            "online": True,
            "shareUsersInfo": [],
            "groups": [],
            "devGroups": [],
            "deviceid": "1001238ef0",
            "name": "Power",
            "params": {
                "init": 1,
                "switch": "on",
                "startup": "off",
                "pulse": "off",
                "pulseWidth": 500,
                "power": "753.90",
                "voltage": "225.40",
                "current": "3.34",
                "oneKwh": "get",
                "uiActive": 60,
                "hundredDaysKwh": "get",
                "endTime": "",
                "startTime": "2021-06-15T22:33:38.131Z",
            },
            "tags": {"m_5378_bran": "on"},
            "sharedTo": [],
            "productModel": "POW",
            "uiid": 32,
        }

        device = SonoffDevice(data)
        self.assertEqual(device.name, "Power")
        self.assertEqual(device.device_id, "1001238ef0")
        self.assertEqual(device.channels, 1)
        self.assertEqual(device.available, True)
        self.assertEqual(device.switches, [True])
        self.assertEqual(device.power, 753.90)
        self.assertEqual(device.current, 3.34)
        self.assertEqual(device.voltage, 225.40)
        self.assertEqual(str(device), "[1001238ef0] Power on")
