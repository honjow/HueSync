from enum import Enum
from dataclasses import dataclass


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


@dataclass
class RGBModeCapabilities:
    """
    Describes the capabilities of an RGB mode.
    描述 RGB 模式的功能支持情况。
    """
    mode: RGBMode
    supports_color: bool = False  # Whether the mode supports setting a primary color
    supports_color2: bool = False  # Whether the mode supports setting a secondary color
    supports_speed: bool = False  # Whether the mode supports adjusting animation speed


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
