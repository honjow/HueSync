from typing import Literal

import lib_hid as hid
from utils import Color, RGBMode

from .hhd_hid_base import RGB_APPLY, RGB_INIT, RGB_SET, RgbMode, buf

"""
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/rog_ally/hid.py 
"""


Zone = Literal["all", "left_left", "left_right", "right_left", "right_right"]
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


def rgb_command(
    zone: Zone,
    mode: RgbMode,
    direction,
    speed: str,
    red: int,
    green: int,
    blue: int,
    o_red: int,
    o_green: int,
    o_blue: int,
):
    c_direction = 0x00
    set_speed = True

    match mode:
        case "solid":
            # Static
            c_mode = 0x00
            set_speed = False
        case "pulse":
            # Strobing
            # c_mode = 0x0A
            # Spiral is agressive
            # Use breathing instead
            # Breathing
            c_mode = 0x01
            o_red = 0
            o_green = 0
            o_blue = 0
        case "rainbow":
            # Color cycle
            c_mode = 0x02
        case "spiral":
            # Rainbow
            c_mode = 0x03
            red = 0
            green = 0
            blue = 0
            if direction == "left":
                c_direction = 0x01
        case "duality":
            # Breathing
            c_mode = 0x01
        # case "direct":
        #     # Direct/Aura
        #     c_mode = 0xFF
        # Should be used for dualsense emulation/ambilight stuffs
        case _:
            c_mode = 0x00

    c_speed = 0xE1
    if set_speed:
        match speed:
            case "low":
                c_speed = 0xE1
            case "medium":
                c_speed = 0xEB
            case _:  # "high"
                c_speed = 0xF5

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
            c_speed if mode != "solid" else 0x00,
            c_direction,
            0x00,  # breathing
            o_red,  # these only affect the breathing mode
            o_green,
            o_blue,
        ]
    )


def rgb_set(
    side: str,
    mode: RgbMode,
    direction: str,
    speed: str,
    red: int,
    green: int,
    blue: int,
    red2: int,
    green2: int,
    blue2: int,
):
    match side:
        case "left_left" | "left_right" | "right_left" | "right_right":
            return [
                rgb_command(
                    side, mode, direction, speed, red, green, blue, red2, green2, blue2
                ),
            ]
        case "left":
            return [
                rgb_command(
                    "left_left",
                    mode,
                    direction,
                    speed,
                    red,
                    green,
                    blue,
                    red2,
                    green2,
                    blue2,
                ),
                rgb_command(
                    "left_right",
                    mode,
                    direction,
                    speed,
                    red,
                    green,
                    blue,
                    red2,
                    green2,
                    blue2,
                ),
            ]
        case "right":
            return [
                rgb_command(
                    "right_right",
                    mode,
                    direction,
                    speed,
                    red,
                    green,
                    blue,
                    red2,
                    green2,
                    blue2,
                ),
                rgb_command(
                    "right_left",
                    mode,
                    direction,
                    speed,
                    red,
                    green,
                    blue,
                    red2,
                    green2,
                    blue2,
                ),
            ]
        case _:
            return [
                rgb_command(
                    "all", mode, direction, speed, red, green, blue, red2, green2, blue2
                ),
            ]


class AsusLEDDeviceHID:
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
            if (
                device["usage_page"] in self._usage_page
                and device["usage"] in self._usage
            ):
                self.hid_device = hid.Device(path=device["path"])
                return True

        return False

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
        init: bool = False,
        global_init: bool = False,
    ) -> bool:
        if not self.is_ready():
            return False

        k_direction = "left"
        k_speed = "low"
        k_brightness = "high"

        # solid
        msg = rgb_set(
            "all",
            "solid",
            k_direction,
            k_speed,
            main_color.R,
            main_color.G,
            main_color.B,
            0,
            0,
            0,
        )
        msg = [
            rgb_set_brightness(k_brightness),
            *msg,
        ]

        if init:
            # Init should switch modes
            msg = [
                *msg,
                RGB_SET,
                RGB_APPLY,
            ]
        if global_init or init:
            msg = [
                *RGB_INIT,
                *msg,
            ]

        for m in msg:
            self.hid_device.write(m)

        return True
