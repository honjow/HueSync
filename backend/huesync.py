import os
from config import IS_LED_SUPPORTED, LED_PATH, logging
from ec import EC
import time


class Joystick:
    Left = 1
    Right = 2
    ALL = 3


class LedPosition:
    Right = 1
    Bottom = 2
    Left = 3
    Top = 4


class Color:
    def __init__(self, r, g, b):
        self.R = r
        self.G = g
        self.B = b


class LedControl:
    @staticmethod
    def set_all_pixels(color: Color, brightness: int = 100):
        # new method
        if IS_LED_SUPPORTED:
            for x in range(2):
                with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                    _brightness : int = brightness * 255 // 100
                    logging.debug(f"brightness={_brightness}")
                    f.write(str(_brightness))
                with open(os.path.join(LED_PATH, "multi_intensity"), "w") as f:
                    f.write(f"{color.R} {color.G} {color.B}")
            return
        
        
        # color = color * brightness // 100
        color = Color(color.R * brightness // 100, color.G * brightness // 100, color.B * brightness // 100)

        LedControl.set_pixel(Joystick.ALL, LedPosition.Right, color)
        LedControl.set_pixel(Joystick.ALL, LedPosition.Bottom, color)
        LedControl.set_pixel(Joystick.ALL, LedPosition.Left, color)
        LedControl.set_pixel(Joystick.ALL, LedPosition.Top, color)

        # AyaLed.set_pixel(Joystick.Right, LedPosition.Right, color)
        # AyaLed.set_pixel(Joystick.Right, LedPosition.Bottom, color)
        # AyaLed.set_pixel(Joystick.Right, LedPosition.Left, color)
        # AyaLed.set_pixel(Joystick.Right, LedPosition.Top, color)

    @staticmethod
    def set_pixel(js, led, color: Color):
        LedControl.set_subpixel(js, led * 3, color.R)
        LedControl.set_subpixel(js, led * 3 + 1, color.G)
        LedControl.set_subpixel(js, led * 3 + 2, color.B)

    @staticmethod
    def set_subpixel(js, subpixel_idx, brightness):
        logging.debug(f"js={js} subpixel_idx={subpixel_idx},brightness={brightness}")
        LedControl.ec_cmd(js, subpixel_idx, brightness)

    @staticmethod
    def ec_cmd(cmd, p1, p2):
        for x in range(2):
            EC.Write(0x6D, cmd)
            EC.Write(0xB1, p1)
            EC.Write(0xB2, p2)
            EC.Write(0xBF, 0x10)
            # time.sleep(0.01)
            EC.Write(0xBF, 0xFF)
            # time.sleep(0.01)
