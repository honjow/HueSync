from enum import Enum


class AyaJoystick(Enum):
    Left = 1
    Right = 2
    ALL = 3


class AyaLedPosition(Enum):
    Right = 1
    Bottom = 2
    Left = 3
    Top = 4


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


class LEDLevel(Enum):
    SolidColor = 1
    Rainbow = 2
