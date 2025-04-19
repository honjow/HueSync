from typing import Literal

"""
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/legion_go/slim/hid.py
"""

Controller = Literal["left", "right"]
RgbMode = Literal["solid", "pulse", "dynamic", "spiral"]


def to_bytes(s: str):
    return bytes.fromhex(s.replace(" ", ""))


def rgb_set_profile(
    profile: Literal[1, 2, 3],
    mode: RgbMode,
    red: int,
    green: int,
    blue: int,
    brightness: float = 1,
    speed: float = 1,
):
    assert profile in (1, 2, 3), f"Invalid profile '{profile}' selected."

    match mode:
        case "solid":
            r_mode = 0
        case "pulse":
            r_mode = 1
        case "dynamic":
            r_mode = 2
        case "spiral":
            r_mode = 3
        case _:
            assert False, f"Mode '{mode}' not supported. "

    r_brightness = min(max(int(64 * brightness), 0), 63)
    r_speed = min(max(int(64 * speed), 0), 63)

    return bytes(
        [
            0x10,
            profile + 2,
            r_mode,
            red,
            green,
            blue,
            r_brightness,
            r_speed,
        ]
    )


def rgb_load_profile(
    profile: Literal[1, 2, 3],
):
    return bytes([0x10, 0x02, profile])


def rgb_enable(enable: bool):
    r_enable = enable & 0x01
    return bytes([0x04, 0x06, r_enable])


def controller_legion_swap(enabled):
    return [to_bytes(f"0506 69 0401 {'02' if enabled else '01'} 01")]


def rgb_multi_load_settings(
    mode: RgbMode,
    profile: Literal[1, 2, 3],
    red: int,
    green: int,
    blue: int,
    brightness: float = 1,
    speed: float = 1,
    init: bool = True,
):
    base = [
        rgb_set_profile(profile, mode, red, green, blue, brightness, speed),
    ]
    # Always update
    if not init:
        return base

    return [
        rgb_enable(True),
        rgb_load_profile(profile),
        *base,
    ]
