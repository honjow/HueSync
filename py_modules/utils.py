import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class AyaJoystickGroup(Enum):
    Left = 1
    Right = 2
    ALL = 3
    Bottom = 4


class AyaLedZone(Enum):
    Right = 1
    Bottom = 2
    Left = 3
    Top = 4


class RGBMode(Enum):
    Disabled = "disabled"
    Solid = "solid"
    Rainbow = "rainbow"
    Pulse = "pulse"  # Breathing effect
    Spiral = "spiral"  # Rotating effect
    Duality = "duality"
    Battery = "battery"


@dataclass
class RGBModeCapabilities:
    """
    Describes the capabilities of an RGB mode.
    描述 RGB 模式的功能支持情况。
    """

    mode: RGBMode
    color: bool = False  # Whether the mode supports setting a primary color
    color2: bool = False  # Whether the mode supports setting a secondary color
    speed: bool = False  # Whether the mode supports adjusting animation speed
    brightness: bool = False  # Whether the mode supports adjusting brightness


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.R = self._validate_color_value(r)
        self.G = self._validate_color_value(g)
        self.B = self._validate_color_value(b)

    def _validate_color_value(self, value: int) -> int:
        if 0 <= value <= 255:
            return value
        raise ValueError("Color values must be between 0 and 255")

    def hex(self):
        return f"{self.R:02X}{self.G:02X}{self.B:02X}"

    def __str__(self):
        return f"Color(R={self.R}, G={self.G}, B={self.B})"

    def __eq__(self, other):
        """比较两个颜色是否相等"""
        if not isinstance(other, Color):
            return False
        return self.R == other.R and self.G == other.G and self.B == other.B


def _find_battery_device() -> Optional[str]:
    """
    查找系统中的电池设备

    Returns:
        Optional[str]: 电池设备名称，如果未找到则返回 None
    """
    power_supply_path = "/sys/class/power_supply"
    try:
        for device in os.listdir(power_supply_path):
            device_type_path = os.path.join(power_supply_path, device, "type")
            if os.path.exists(device_type_path):
                with open(device_type_path, "r") as f:
                    if f.read().strip() == "Battery":
                        return device
        return None
    except (FileNotFoundError, IOError):
        return None


def get_battery_info() -> Tuple[int, bool]:
    """
    获取电池信息

    Returns:
        Tuple[int, bool]: (电量百分比, 是否正在充电)
        电量百分比: 0-100，如果无法获取则返回 -1
        是否充电: True 表示正在充电，False 表示未充电或无法获取
    """
    battery_device = _find_battery_device()
    if not battery_device:
        return -1, False

    power_supply_path = "/sys/class/power_supply"
    battery_path = os.path.join(power_supply_path, battery_device)

    # Get battery capacity | 获取电量
    try:
        with open(os.path.join(battery_path, "capacity"), "r") as f:
            percentage = int(f.read().strip())
            if not 0 <= percentage <= 100:
                percentage = -1
    except (FileNotFoundError, ValueError, IOError):
        percentage = -1

    # Get charging status | 获取充电状态
    try:
        with open(os.path.join(battery_path, "status"), "r") as f:
            status = f.read().strip()
            is_charging = status == "Charging"
    except (FileNotFoundError, IOError):
        is_charging = False

    return percentage, is_charging


def get_battery_percentage() -> int:
    """
    获取设备当前电量百分比

    Returns:
        int: 电量百分比（0-100），如果无法获取则返回 -1
    """
    percentage, _ = get_battery_info()
    return percentage


def is_battery_charging() -> bool:
    """
    检查设备是否正在充电

    Returns:
        bool: 如果正在充电返回 True，否则返回 False
    """
    _, is_charging = get_battery_info()
    return is_charging
