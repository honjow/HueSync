"""
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/oxp/hid_v2.py
"""

from typing import Literal


def gen_cmd(cid: int, cmd: bytes | list[int] | str, size: int = 64):
    # Command: [idx, cid, 0x3f, *cmd, 0x3f, cid], idx is optional
    if isinstance(cmd, str):
        c = bytes.fromhex(cmd)
    else:
        c = bytes(cmd)
    base = bytes([cid, 0xFF, *c])
    return base + bytes([0] * (size - len(base)))


def gen_rgb_mode(
    mode: Literal[
        "monster_woke",
        "flowing",
        "sunset",
        "neon",
        "dreamy",
        "cyberpunk",
        "colorful",
        "aurora",
        "sun",
    ],
):
    mc = 0
    match mode:
        case "monster_woke":
            mc = 0x0D
        case "flowing":
            mc = 0x03
        case "sunset":
            mc = 0x0B
        case "neon":
            mc = 0x05
        case "dreamy":
            mc = 0x07
        case "cyberpunk":
            mc = 0x09
        case "colorful":
            mc = 0x0C
        case "aurora":
            mc = 0x01
        case "sun":
            mc = 0x08
    return gen_cmd(0x07, [mc])


def gen_intercept(enable: bool):
    return gen_cmd(0xB2, [0x03 if enable else 0x00, 0x01, 0x02])


def gen_brightness(
    enabled: bool,
    brightness: Literal["low", "medium", "high"],
):
    match brightness:
        case "low":
            bc = 0x01
        case "medium":
            bc = 0x03
        case _:  # "high":
            bc = 0x04

    return gen_cmd(0x07, [0xFD, enabled, 0x05, bc])


def gen_rgb_solid(r, g, b):
    return gen_cmd(0x07, [0xFE] + 20 * [r, g, b] + [0x00])


KBD_NAME = "keyboard"
HOME_NAME = "guide"
KBD_NAME_NON_TURBO = "share"
KBD_HOLD = 0.2
OXP_BUTTONS = {
    0x24: KBD_NAME,
    0x21: HOME_NAME,
    0x22: "extra_l1",
    0x23: "extra_r1",
}


INITIALIZE = [
    # gen_cmd(
    #     0xF5,
    #     "010238020101010101000000020102000000030103000000040104000000050105000000060106000000070107000000080108000000090109000000",
    # ),
    # gen_cmd(
    #     0xF5,
    #     "0102380202010a010a0000000b010b0000000c010c0000000d010d0000000e010e0000000f010f000000100110000000220200000000230200000000",
    # ),
    # gen_intercept(False),
]
