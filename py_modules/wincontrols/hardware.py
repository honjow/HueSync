#!/usr/bin/env python3

import struct

from wincontrols.config import *

import wincontrols.gpd_hid as gpd_hid

class WinControls():
    """Class for reading and writing configuration to the GPD Win controller hardware."""

    # Map of fields and their offsets in the binary configuration
    _fields = [
        # left stick
        Key(16,'lu','left stick up'),
        Key(18,'ld','left stick down'),
        Key(20,'ll','left stick left'),
        Key(22,'lr','left stick right'),

        # dpad
        Key(0,'du','dpad up'),
        Key(2,'dd','dpad down'),
        Key(4,'dl','dpad left'),
        Key(6,'dr','dpad right'),

        # ABXY
        Key(8,'a','A button'),
        Key(10,'b','B button'),
        Key(12,'x','X button'),
        Key(14,'y','Y button'),

        # shoulder buttons
        Key(34,'l1','L1 shoulder button'),
        Key(36,'r1','R1 shoulder button'),

        Key(38,'l2','L2 trigger'),
        Key(40,'r2','R2 trigger'),

        # stick clicks
        Key(24,'l3','left stick click'),
        Key(26,'r3','right stick click'),

        # start select and menu
        Key(28,'start','Start button'),
        Key(30,'select','Select button'),
        Key(32,'menu','Menu button'),

        # macro keys
        Key(50,'l41','L4 macro key 1'),
        Key(52,'l42','L4 macro key 2'),
        Key(54,'l43','L4 macro key 3'),
        Key(56,'l44','L4 macro key 4'),

        Key(58,'r41','R4 macro key 1'),
        Key(60,'r42','R4 macro key 2'),
        Key(62,'r43','R4 macro key 3'),
        Key(64,'r44','R4 macro key 4'),

        Rumble(66,'rumble','Rumble'),
        LedMode(68,'ledmode','LED mode'),
        Colour(69,'colour','LED colour'),

        # deadzone and centering
        Signed(72,'ldead','Left stick deadzone'),
        Signed(73,'lcent','Left stick centering'),
        Signed(74,'rdead','Right stick deadzone'),
        Signed(75,'rcent','Right stick centering'),

        # macro delays
        Millis(80,'l4delay1','L4 macro delay 1'),
        Millis(82,'l4delay2','L4 macro delay 2'),
        Millis(84,'l4delay3','L4 macro delay 3'),
        Millis(86,'l4delay4','L4 macro delay 4'),
        Millis(88,'r4delay1','R4 macro delay 1'),
        Millis(90,'r4delay2','R4 macro delay 2'),
        Millis(92,'r4delay3','R4 macro delay 3'),
        Millis(94,'r4delay4','R4 macro delay 4'),
    ]

    field = {f.name: f for f in _fields}

    def __init__(self, read=True, disableFwCheck=False):
        self.disableFwCheck = disableFwCheck
        self._openHid()
        self.loaded = False
        if read:
            self.readConfig()

    def _openHid(self):
        self.device = None
        for dev in gpd_hid.enumerate(vid=0x2f24):
            if dev['usage_page'] == 0xff00:
                #print(dev['path'])
                self.device = gpd_hid.Device(path=dev['path'])
                break
        if not self.device:
            raise RuntimeError("Unable to open GPD controller device")

    def _cdata(self, configRaw: bytearray, index):
        return bytes(struct.pack("<H",index)) + configRaw[index<<4:(index+1)<<4]

    def _checksum(self, configRaw: bytearray):
        return sum(configRaw)

    def _parseConfig(self, configRaw: bytearray):
        for field in self._fields:
            field.decode(configRaw)
        self.loaded = True

    def _generateConfig(self):
        if not self.loaded:
            raise RuntimeError("No config loaded")

        configRaw = bytearray(256)
        for field in self._fields:
            field.apply(configRaw)
        return configRaw

    def _parseResponse(self, response):
        info = struct.unpack_from("<8xBBBBB11xII", response)
        return {
            'ready': info[0],
            'Xfirmware': f"X{info[1]:x}{info[2]:02x}",
            'Kfirmware': f"K{info[3]:x}{info[4]:02x}",
            'checksum': info[5]
        }

    def _checkDevice(self):
        if self.disableFwCheck:
            return
        supported = ['K504', 'K407']
        info = self._parseResponse(self._response)
        if info['Kfirmware'] not in supported:
            raise RuntimeError(f"Unsupported firmware version: {info['Xfirmware']}{info['Kfirmware']}")

    def _waitReady(self, id):
        self._response = None
        while self._response is None or self._response[8] != 0xaa:
            self._response = self._sendReq(id)
        self._checkDevice()

    def _sendReq(self,id,data=None):
        result = bytearray([0x01, 0xa5, id, 0x5a, id^0xFF, 00])

        if (data):
            result.extend(data)
        result.extend(bytearray(33-len(result)))

        self.device.send_feature_report(bytes(result))

        #print("Sent: %s" % result.hex())
        if (id != 0x21 and id != 0x23): # writes don't have replies
            result = self.device.get_input_report(1,65)
            #print("Recv: %s" % result.hex())
            return result

    def readConfig(self):
        """Read the current configuration from the device."""
        self.loaded = False

        self._waitReady(0x10)

        configRaw = bytearray()
        for addr in range(4):
            configRaw.extend(self._sendReq(0x11,[addr]))

        self._response = self._sendReq(0x12)
        if self._parseResponse(self._response)['checksum'] == self._checksum(configRaw):
            self._parseConfig(configRaw)
        else:
            raise RuntimeError("Checksum error reading config")

    def writeConfig(self):
        """Write the current configuration to the device."""
        configRaw = self._generateConfig()

        self._waitReady(0x20)

        for block in range(8):
            self._sendReq(0x21,self._cdata(configRaw, block))

        self._response = self._sendReq(0x22)
        if self._parseResponse(self._response)['checksum'] == self._checksum(configRaw):
            # valid checksum so commit config
            self._sendReq(0x23)
        else:
            raise RuntimeError("Checksum error writing config")

    def setConfig(self, config):
        """Update the configuration from a list or newline separated string of key=value pairs"""
        if type(config) == str:
            config = config.split("\n")

        for line in config:
            if line == "" or line.startswith("#"):
                continue
            if "=" not in line:
                raise RuntimeError("Invalid config line: %s" % line)

            key, value = line.split("=")

            key = key.strip().lower()

            if not key in self.field:
                raise RuntimeError("Invalid config key: %s" % key)

            self.field[key].set(value)

        return True

    def dump(self):
        """Return the current configuration as a string"""
        return "\n".join(map(str, self._fields))
