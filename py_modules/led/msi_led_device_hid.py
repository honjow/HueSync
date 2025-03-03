from itertools import chain, repeat

import lib_hid as hid
from config import logger
from utils import Color, RGBMode


class MsiLEDDeviceHID:
    def __init__(self, vid, pid):
        self._vid = vid
        self._pid = pid
        self.hid_device = None

    def is_ready(self) -> bool:
        # Prepare list for all HID devices
        hid_device_list = hid.enumerate(self._vid, self._pid)

        # Check every HID device to find LED device
        for device in hid_device_list:
            # logger.info(f"device={device}")
            if device["interface_number"] == 3:
                self.hid_device = hid.Device(path=device["path"])
                return True

        return False

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
    ) -> bool:
        if not self.is_ready():
            return False

        prefix = [0x0F, 0x00, 0x00, 0x3C, 0x21, 0x01]
        LEDOption = [0x01, 0xFF, 0x1B]
        rgbData = [0x00]
        suffix = [0x00]

        if mode == RGBMode.Solid:
            led_color = main_color
            LEDOption = [0x01, 0xFF, 0x1B]
            rgbData = list(repeat([led_color.R, led_color.G, led_color.B], 9))

        elif mode == RGBMode.Disabled:
            # 01 fd 1c 14 64
            LEDOption = [0x01, 0xFD, 0x1C, 0x14, 0x64]

        elif mode == RGBMode.Rainbow:
            LEDOption = [0x03]
            rgbData = list(repeat(0x00, 60))

        else:
            return False

        msg = list(chain(prefix, LEDOption, chain(*rgbData), suffix))
        msg_hex = "".join([f"{x:02X}" for x in msg])
        logger.info(f"msg={msg_hex}")
        result: bytearray = bytearray(msg)

        self.hid_device.write(bytes(result))

        return True
