"""
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/oxp/hid_v1.py
"""

from typing import Literal


def gen_cmd(cid: int, cmd: bytes | list[int] | str, idx: int = 0x01, size: int = 64):
    # Command: [idx, cid, 0x3f, *cmd, 0x3f, cid], idx is optional
    if isinstance(cmd, str):
        c = bytes.fromhex(cmd)
    else:
        c = bytes(cmd)
    base = bytes([cid, 0x3F, idx, *c])
    return base + bytes([0] * (size - len(base) - 2)) + bytes([0x3F, cid])


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
    return gen_cmd(0xB8, [mc, 0x00, 0x02])


def gen_intercept(enable: bool):
    return gen_cmd(0xB2, [0x03 if enable else 0x00, 0x01, 0x02])


def gen_brightness(
    side: Literal[0, 3, 4],
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

    return gen_cmd(0xB8, [0xFD, 0x00, 0x02, enabled, 0x05, bc])


# Sides on the g1
# 1 = left controller
# 2 = right controller
# 3 = center V
# 4 = touch keyboard
# 5 = device color on the front (triangle)
def gen_rgb_solid(r, g, b, side: int = 0x00):
    return gen_cmd(0xB8, [0xFE, side, 0x02] + 18 * [r, g, b] + [r, g])


KBD_NAME = "keyboard"
HOME_NAME = "guide"
KBD_NAME_NON_TURBO = "share"
KBD_HOLD = 0.12
OXP_BUTTONS = {
    0x24: KBD_NAME,
    0x21: HOME_NAME,
    0x22: "extra_l1",
    0x23: "extra_r1",
}


INITIALIZE = [
    gen_cmd(
        0xB4,
        "0238020101010101000000020102000000030103000000040104000000050105000000060106000000070107000000080108000000090109000000",
    ),
    gen_cmd(
        0xB4,
        "02380202010a010a0000000b010b0000000c010c0000000d010d0000000e010e0000000f010f000000100110000000220200000000230200000000",
    ),
    gen_intercept(False),
]
