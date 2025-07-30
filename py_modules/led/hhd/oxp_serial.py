"""
code from https://github.com/hhd-dev/hhd/blob/master/src/hhd/device/oxp/serial.py
"""

import os
import subprocess
from typing import Literal

import utils
from config import logger


def gen_cmd(
    cid: int, cmd: bytes | list[int] | str, idx: int | None = None, size: int = 64
):
    # Command: [idx, cid, 0x3f, *cmd, 0x3f, cid], idx is optional
    if isinstance(cmd, str):
        c = bytes.fromhex(cmd)
    else:
        c = bytes(cmd)
    base = bytes([cid, 0x3F, *c])
    if idx is not None:
        base = bytes([idx]) + base
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
    return gen_cmd(0xFD, [0x00, mc])


def gen_intercept(enable: bool):
    return gen_cmd(0xA1, 2 * [int(enable)], idx=0x00)


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

    return gen_cmd(
        0xFD, [side, 0xFD, 0x00 if side else 0x03, 0x00, int(enabled), 0x05, bc]
    )


def gen_rgb_solid(r, g, b, side: Literal[0x00, 0x03, 0x04] = 0x00):
    start = [side, 0xFE, 0x00, 0x00]
    end = [r, g]
    return gen_cmd(0xFD, start + 18 * [r, g, b] + end)


KBD_NAME = "keyboard"
KBD_NAME_NON_TURBO = "share"
KBD_HOLD = 0.12
OXP_BUTTONS = {
    0x24: KBD_NAME,
    0x22: "extra_l1",
    0x23: "extra_r1",
}


INITIALIZE = [
    # gen_intercept(True),
    gen_cmd(
        0xF5,
        "0000000001010101000000020102000000030103000000040104000000050105000000060106000000070107000000080108000000090109000000",
        idx=0x01,
    ),
    gen_cmd(
        0xF5,
        "00000000010a010a0000000b010b0000000c010c0000000d010d0000000e010e0000000f010f000000100110000000220200000000230200000000",
        idx=0x02,
    ),
    # gen_intercept(False), # does not seem to be needed
]

INIT_DELAY = 2
WRITE_DELAY = 0.05
SCAN_DELAY = 1

_mappings_init = True


def get_serial():

    VID = "1a86"
    PID = "7523"

    dev = None
    buttons_only = False
    for d in os.listdir("/dev"):
        if not d.startswith("ttyUSB"):
            continue

        path = os.path.join("/dev", d)

        out = subprocess.run(
            ["udevadm", "info", "--name", path],
            check=True,
            capture_output=True,
            text=True,
            env=utils.get_env(),
        )

        if f"ID_VENDOR_ID={VID}" not in out.stdout:
            continue

        if f"ID_MODEL_ID={PID}" not in out.stdout:
            continue

        dev = path
        break

    for d in os.listdir("/dev"):
        if not d.startswith("ttyS"):
            continue

        path = os.path.join("/dev", d)

        out = subprocess.run(
            ["udevadm", "info", "--name", path],
            check=True,
            capture_output=True,
            text=True,
            env=utils.get_env(),
        )

        # OneXFly device is pnp
        if "devices/pnp" not in out.stdout:
            continue

        # TODO: We need to get a baseline to quirk this type properly
        logger.info(f"Serial port information:\n{out.stdout}")

        dev = path
        buttons_only = True
        break
    return dev, buttons_only


def init_serial():
    import serial

    dev, buttons_only = get_serial()

    if not dev:
        logger.warning("OXP CH340 serial device not found.")
        return None, buttons_only

    logger.info(f"OXP CH340 serial device found at {dev}")

    ser = serial.Serial(
        dev,
        115200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.EIGHTBITS,
        timeout=0,
        exclusive=True,
    )

    return ser, buttons_only
