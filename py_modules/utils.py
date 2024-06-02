from enum import Enum


class AyaJoystick:
    Left = 1
    Right = 2
    ALL = 3


class AyaLedPosition:
    Right = 1
    Bottom = 2
    Left = 3
    Top = 4


class Color:
    def __init__(self, r, g, b):
        self.R = r
        self.G = g
        self.B = b

    def hex(self):
        return f"{self.R:02x}{self.G:02x}{self.B:02x}"
    
    def __str__(self):
        return f"Color(R={self.R}, G={self.G}, B={self.B})"


class LEDLevel(Enum):
    SolidColor = 1
    Rainbow = 2
