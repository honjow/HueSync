from typing import Literal
import hid
from utils import Color, LEDLevel
from config import logger

'''
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/rog_ally/hid.py 
'''

def buf(x):
    return bytes(x) + bytes(64 - len(x))

Zone = Literal["all", "left_left", "left_right", "right_left", "right_right"]
RgbMode = Literal["solid", "pulse", "dynamic", "spiral"]
GamepadMode = Literal["default", "mouse", "macro"]
Brightness = Literal["off", "low", "medium", "high"]

def rgb_set_brightness(brightness: Brightness):
    match brightness:
        case "high":
            c = 0x03
        case "medium":
            c = 0x02
        case "low":
            c = 0x01
        case _:
            c = 0x00
    return buf([0x5A, 0xBA, 0xC5, 0xC4, c])

def rgb_command(zone: Zone, mode: RgbMode, red: int, green: int, blue: int):
    match mode:
        case "solid":
            # Static
            c_mode = 0x00
        case "pulse":
            # Breathing
            c_mode = 0x01
        case "dynamic":
            # Color cycle
            c_mode = 0x02
        case "spiral":
            # Rainbow
            c_mode = 0x03
        # case "adsf":
        #     # Strobing
        #     c_mode = 0x0A
        # case "asdf":
        #     # Direct (?)
        #     c_mode = 0xFF
        case _:
            c_mode = 0x00

    match zone:
        case "left_left":
            c_zone = 0x01
        case "left_right":
            c_zone = 0x02
        case "right_left":
            c_zone = 0x03
        case "right_right":
            c_zone = 0x04
        case _:
            c_zone = 0x00

    return buf(
        [
            0x5A,
            0xB3,
            c_zone,  # zone
            c_mode,  # mode
            red,
            green,
            blue,
            0x00,  # speed
            0x00,  # direction
            0x00,  # breathing
            red,
            green,
            blue,
        ]
    )

def rgb_set(
    side: Literal["main", "left", "right"],
    mode: RgbMode,
    red: int,
    green: int,
    blue: int,
):
    match side:
        case "left":
            return [
                rgb_command("left_left", mode, red, green, blue),
                rgb_command("left_right", mode, red, green, blue),
            ]
        case "right":
            return [
                rgb_command("right_right", mode, red, green, blue),
                rgb_command("right_left", mode, red, green, blue),
            ]
        case _:
            return [
                rgb_command("all", mode, red, green, blue),
            ]

class AsusLEDDevice:
    def __init__(self, vid, pid, usage_page, usage):
        self._vid = vid
        self._pid = pid
        self._usage_page = usage_page
        self._usage = usage
        self.hid_device = None

    def is_ready(self) -> bool:
        # Prepare list for all HID devices
        hid_device_list = hid.enumerate(self._vid, self._pid)

        # Check every HID device to find LED device
        for device in hid_device_list:
            if device["usage_page"] in self._usage_page and device["usage"] in self._usage:
                self.hid_device = hid.Device(path=device["path"])
                return True

        return False

    def set_led_color(
        self,
        main_color: Color,
        brightness: int,
        level: LEDLevel,
    ) -> bool:
        if not self.is_ready():
            return False

        msg = rgb_set("main", "solid", main_color.R, main_color.G, main_color.B)
        msg = [
            rgb_set_brightness("medium"),
            *msg,
        ]

        for m in msg:
            self.hid_device.write(m)

        return True
