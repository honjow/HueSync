from typing import Literal

from .hhd_hid_base import RgbMode, buf


"""
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/rog_ally/hid.py 
"""

FEATURE_KBD_DRIVER = 0x5A
FEATURE_KBD_APP = 0x5D
FEATURE_KBD_ID = FEATURE_KBD_DRIVER


def RGB_PKEY_INIT(key):
    return [
        buf(
            [
                key,
                0x41,
                0x53,
                0x55,
                0x53,
                0x20,
                0x54,
                0x65,
                0x63,
                0x68,
                0x2E,
                0x49,
                0x6E,
                0x63,
                0x2E,
            ]
        ),
    ]


RGB_APPLY = buf([FEATURE_KBD_ID, 0xB4])
RGB_SET = buf([FEATURE_KBD_ID, 0xB5])
RGB_INIT = RGB_PKEY_INIT(FEATURE_KBD_ID)


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
    return buf([FEATURE_KBD_ID, 0xBA, 0xC5, 0xC4, c])


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
            FEATURE_KBD_ID,
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
