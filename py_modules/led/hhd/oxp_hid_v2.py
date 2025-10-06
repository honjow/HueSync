"""
OneXPlayer HID Protocol Version 2
Used by XFly, Mini Pro, A1X series

Ported from HHD: hhd/device/oxp/hid_v2.py
基于HHD移植：适用于XFly、Mini Pro、A1X系列
"""

from typing import Literal


def gen_cmd(cid: int, cmd: bytes | list[int] | str, size: int = 64) -> bytes:
    """
    Generate HID command for v2 protocol.
    生成v2协议的HID命令。
    
    Command format: [cid, 0xFF, *cmd, 0x00...]
    命令格式：[cid, 0xFF, *cmd, 0x00...]
    
    Args:
        cid: Command ID
        cmd: Command data (bytes, list, or hex string)
        size: Total command size (default 64 bytes)
        
    Returns:
        bytes: Complete HID command
    """
    if isinstance(cmd, str):
        c = bytes.fromhex(cmd)
    else:
        c = bytes(cmd)
    
    base = bytes([cid, 0xFF, *c])
    return base + bytes([0] * (size - len(base)))


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
    - aok (0x0E) - AOKZOE specific
    
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
        "aok": 0x0E,
    }
    mc = mode_map.get(mode, 0x01)  # Default to aurora
    return gen_cmd(0x07, [mc])


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
    enabled: bool,
    brightness: Literal["low", "medium", "high"],
) -> bytes:
    """
    Generate brightness control command.
    生成亮度控制命令。
    
    Note: V2 protocol does not support zone-specific brightness.
    注意：V2协议不支持分区亮度控制。
    
    Args:
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
    
    return gen_cmd(0x07, [0xFD, int(enabled), 0x05, bc])


def gen_rgb_solid(r: int, g: int, b: int) -> bytes:
    """
    Generate solid color RGB command.
    生成纯色RGB命令。
    
    Note: V2 protocol does not support zone-specific colors.
    注意：V2协议不支持分区颜色控制。
    
    Args:
        r, g, b: RGB color values (0-255)
        
    Returns:
        bytes: RGB solid color command
    """
    return gen_cmd(0x07, [0xFE] + 20 * [r, g, b] + [0x00])


# V2 devices typically don't need initialization
# V2设备通常不需要初始化命令
INITIALIZE = []
