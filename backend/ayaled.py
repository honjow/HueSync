import os
from config import IS_LED_SUPPORTED, LED_PATH
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

class Color():
    def __init__(self,r,g,b):
        self.R=r
        self.G=g
        self.B=b

class AyaLed():
    @staticmethod
    def set_all_pixels(color:Color):
        # new method
        if IS_LED_SUPPORTED:
            for x in range(2):
                with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                    f.write("255")
                with open(os.path.join(LED_PATH, "multi_intensity"), "w") as f:
                    f.write(f"{color.R} {color.G} {color.B}")
            return

        AyaLed.set_pixel(Joystick.ALL, LedPosition.Right, color)
        AyaLed.set_pixel(Joystick.ALL, LedPosition.Bottom, color)
        AyaLed.set_pixel(Joystick.ALL, LedPosition.Left, color)
        AyaLed.set_pixel(Joystick.ALL, LedPosition.Top, color)
    
        #AyaLed.set_pixel(Joystick.Right, LedPosition.Right, color)
        #AyaLed.set_pixel(Joystick.Right, LedPosition.Bottom, color)
        #AyaLed.set_pixel(Joystick.Right, LedPosition.Left, color)
        #AyaLed.set_pixel(Joystick.Right, LedPosition.Top, color)

    @staticmethod
    def set_pixel(js, led, color: Color):
        AyaLed.set_subpixel(js, led * 3, color.R)
        AyaLed.set_subpixel(js, led * 3 + 1, color.G)
        AyaLed.set_subpixel(js, led * 3 + 2, color.B)

    @staticmethod
    def set_subpixel(js, subpixel_idx, brightness):
        print(f"js={js} subpixel_idx={subpixel_idx},brightness={brightness}")
        AyaLed.ec_cmd(js,subpixel_idx,brightness)
    
    @staticmethod
    def ec_cmd(cmd, p1, p2):
        for x in range(2):
            EC.Write(0x6d, cmd)
            EC.Write(0xb1, p1)
            EC.Write(0xb2, p2)
            EC.Write(0xbf, 0x10)
            #time.sleep(0.01)
            EC.Write(0xbf, 0xff)
            #time.sleep(0.01)
