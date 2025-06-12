from enum import Enum
from itertools import chain, repeat
from typing import Sequence

import lib_hid as hid
from config import logger
from utils import Color, RGBMode

"""
convert from https://github.com/Valkirie/HandheldCompanion/blob/main/HandheldCompanion/Devices/OneXPlayer/OneXPlayerOneXFly.cs 
"""

X1_MINI_VID = 0x1A86
X1_MINI_PID = 0xFE00
X1_MINI_PAGE = 0xFF00
X1_MINI_USAGE = 0x0001

XFLY_VID = 0x1A2C
XFLY_PID = 0xB001
XFLY_PAGE = 0xFF01
XFLY_USAGE = 0x0001


class Protocol(Enum):
    X1_MINI = 0
    XFLY = 1
    UNKNOWN = 2


class OneXLEDDeviceHID:
    def __init__(
        self,
        vid: Sequence[int] = [],
        pid: Sequence[int] = [],
        usage_page: Sequence[int] = [],
        usage: Sequence[int] = [],
        interface: int | None = None,
    ):
        self._vid = vid
        self._pid = pid
        self._usage_page = usage_page
        self._usage = usage
        self.interface = interface
        self.hid_device = None

    def is_ready(self) -> bool:
        if self.hid_device:
            return True

        hid_device_list = hid.enumerate()

        # Check every HID device to find LED device
        for device in hid_device_list:
            logger.debug(f"device: {device}")
            if device["vendor_id"] not in self._vid:
                continue
            if device["product_id"] not in self._pid:
                continue
            if (
                self.interface is not None
                and device["interface_number"] != self.interface
            ):
                continue
            if (
                device["usage_page"] in self._usage_page
                and device["usage"] in self._usage
            ):
                self.hid_device = hid.Device(path=device["path"])
                logger.debug(
                    f"Found device: {device}, \npath: {device['path']}, \ninterface: {device['interface_number']}"
                )
                return True
        return False

    def _check_protocol(self) -> Protocol:
        if self._vid == X1_MINI_VID and self._pid == X1_MINI_PID:
            return Protocol.X1_MINI
        if self._vid == XFLY_VID and self._pid == XFLY_PID:
            return Protocol.XFLY
        return Protocol.UNKNOWN

    def set_led_brightness(self, brightness: int) -> bool:
        # OneXFly brightness range is: 0 - 4 range, 0 is off, convert from 0 - 100 % range
        brightness = round(brightness / 20)

        # Check if device is available
        if self.hid_device is None:
            return False

        # Define the HID message for setting brightness.
        msg: bytearray = bytearray([0x00, 0x07, 0xFF, 0xFD, 0x01, 0x05, brightness])

        # Write the HID message to set the LED brightness.
        self.hid_device.write(bytes(msg))

        return True

    def set_led_brightness_new(self, brightness: int) -> bool:
        brightness = round(brightness / 20)
        enabled = True
        brightness_level = "high"
        match brightness:
            case 0:
                enabled = False
            case 1:
                brightness_level = "low"
            case 3:
                brightness_level = "medium"
            case _:
                brightness_level = "high"

        if self._check_protocol() == Protocol.X1_MINI:
            from .hhd.oxp_hid_v1 import gen_brightness

            cmd: bytes = gen_brightness(0, enabled, brightness_level)
        else:
            from .hhd.oxp_hid_v2 import gen_brightness

            cmd: bytes = gen_brightness(enabled, brightness_level)

        if self.hid_device is None:
            return False
        cmd_hex = "".join([f"{x:02X}" for x in cmd])
        logger.info(f"cmd={cmd_hex}")
        self.hid_device.write(cmd)
        return True

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
    ) -> bool:
        if not self.is_ready():
            return False

        prefix = [0x00, 0x07, 0xFF]
        LEDOption = [0x00]
        rgbData = [0x00]
        suffix = [0x00]

        if mode == RGBMode.Solid:
            led_color = main_color
            LEDOption = [0xFE]
            rgbData = list(repeat([led_color.R, led_color.G, led_color.B], 20))

        elif mode == RGBMode.Rainbow:
            LEDOption = [0x03]
            rgbData = [list(repeat(0x00, 60))]

        else:
            return False

        msg = list(chain(prefix, LEDOption, chain(*rgbData), suffix))
        msg_hex = "".join([f"{x:02X}" for x in msg])
        logger.info(f"msg={msg_hex}")
        result: bytearray = bytearray(msg)

        if self.hid_device is None:
            return False

        self.hid_device.write(bytes(result))
        # self.hid_device.close()
        return True

    def set_led_color_new(
        self,
        main_color: Color,
        mode: RGBMode,
    ) -> bool:
        if not self.is_ready():
            return False

        if self._check_protocol() == Protocol.X1_MINI:
            from .hhd.oxp_hid_v1 import gen_rgb_mode, gen_rgb_solid
        else:
            from .hhd.oxp_hid_v2 import gen_rgb_mode, gen_rgb_solid

        if mode == RGBMode.Disabled:
            cmd: bytes = gen_rgb_solid(0, 0, 0)
        elif mode == RGBMode.Solid:
            cmd: bytes = gen_rgb_solid(main_color.R, main_color.G, main_color.B)
        elif mode == RGBMode.Rainbow:
            cmd: bytes = gen_rgb_mode("neon")
        else:
            return False

        if self.hid_device is None:
            return False
        cmd_hex = "".join([f"{x:02X}" for x in cmd])
        logger.info(f"cmd={cmd_hex}")
        self.hid_device.write(cmd)
        return True
