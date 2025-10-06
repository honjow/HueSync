"""
OneXPlayer HID Protocol Version 1
Used by X1 Mini, X1 Mini Pro, G1 series

Ported from HHD: hhd/device/oxp/hid_v1.py
基于HHD移植：适用于X1 Mini、X1 Mini Pro、G1系列
"""

from typing import Literal


def gen_cmd(cid: int, cmd: bytes | list[int] | str, idx: int = 0x01, size: int = 64) -> bytes:
    """
    Generate HID command for v1 protocol.
    生成v1协议的HID命令。
    
    Command format: [cid, 0x3F, idx, *cmd, 0x00..., 0x3F, cid]
    命令格式：[cid, 0x3F, idx, *cmd, 0x00..., 0x3F, cid]
    
    Args:
        cid: Command ID
        cmd: Command data (bytes, list, or hex string)
        idx: Index byte (default 0x01)
        size: Total command size (default 64 bytes)
        
    Returns:
        bytes: Complete HID command
    """
    if isinstance(cmd, str):
        c = bytes.fromhex(cmd)
    else:
        c = bytes(cmd)
    
    base = bytes([cid, 0x3F, idx, *c])
    return base + bytes([0] * (size - len(base) - 2)) + bytes([0x3F, cid])


def gen_rgb_mode(mode: str) -> bytes:
    """
    Generate RGB preset mode command.
    生成RGB预设模式命令。
    
    Supported modes:
    - monster_woke (0x0D)
    - flowing (0x03)
    - sunset (0x0B)
    - neon (0x05)
    - dreamy (0x07)
    - cyberpunk (0x09)
    - colorful (0x0C)
    - aurora (0x01)
    - sun (0x08)
    
    Args:
        mode: Mode name string
        
    Returns:
        bytes: RGB mode command
    """
    mode_map = {
        "monster_woke": 0x0D,
        "flowing": 0x03,
        "sunset": 0x0B,
        "neon": 0x05,
        "dreamy": 0x07,
        "cyberpunk": 0x09,
        "colorful": 0x0C,
        "aurora": 0x01,
        "sun": 0x08,
    }
    mc = mode_map.get(mode, 0x01)  # Default to aurora
    return gen_cmd(0xB8, [mc, 0x00, 0x02])


def gen_intercept(enable: bool) -> bytes:
    """
    Generate button intercept command.
    生成按键拦截命令。
    
    Args:
        enable: True to enable intercept, False to disable
        
    Returns:
        bytes: Intercept command
    """
    return gen_cmd(0xB2, [0x03 if enable else 0x00, 0x01, 0x02])


def gen_brightness(
    side: Literal[0, 3, 4],
    enabled: bool,
    brightness: Literal["low", "medium", "high"],
) -> bytes:
    """
    Generate brightness control command.
    生成亮度控制命令。
    
    Args:
        side: LED zone (0=all, 3=center V, 4=touch keyboard)
        enabled: True to enable LEDs, False to disable
        brightness: Brightness level
        
    Returns:
        bytes: Brightness command
    """
    brightness_map = {
        "low": 0x01,
        "medium": 0x03,
        "high": 0x04,
    }
    bc = brightness_map.get(brightness, 0x04)
    
    return gen_cmd(0xB8, [0xFD, 0x00, 0x02, int(enabled), 0x05, bc])


def gen_rgb_solid(r: int, g: int, b: int, side: int = 0x00) -> bytes:
    """
    Generate solid color RGB command.
    生成纯色RGB命令。
    
    For G1 devices, side values:
    - 0x00: All zones
    - 0x01: Left controller
    - 0x02: Right controller
    - 0x03: Center V
    - 0x04: Touch keyboard
    - 0x05: Front panel triangle
    
    Args:
        r, g, b: RGB color values (0-255)
        side: LED zone (default 0x00 for all)
        
    Returns:
        bytes: RGB solid color command
    """
    return gen_cmd(0xB8, [0xFE, side, 0x02] + 18 * [r, g, b] + [r, g])


# Initialization commands for device setup
# 设备设置的初始化命令
INITIALIZE = [
    # Button mapping configuration
    gen_cmd(
        0xB4,
        "0238020101010101000000020102000000030103000000040104000000050105000000060106000000070107000000080108000000090109000000",
    ),
    gen_cmd(
        0xB4,
        "02380202010a010a0000000b010b0000000c010c0000000d010d0000000e010e0000000f010f000000100110000000220200000000230200000000",
    ),
    # Disable button intercept
    gen_intercept(False),
]
