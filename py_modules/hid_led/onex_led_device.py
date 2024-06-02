from math import sqrt
from itertools import repeat
import hid as hid
from utils import Color, LEDLevel


"""
convert from https://github.com/Valkirie/HandheldCompanion/blob/main/HandheldCompanion/Devices/OneXPlayer/OneXPlayerOneXFly.cs 
"""


class OneXLEDDevice:
    def __init__(self, vid, pid):
        self._vid = vid
        self._pid = pid
        self.hid_device = None

    def is_ready(self):
        # Prepare list for all HID devices
        hid_device_list = hid.enumerate(self._vid, self._pid)

        # Check every HID device to find LED device
        for device in hid_device_list:
            # OneXFly device for LED control does not support a FeatureReport, hardcoded to match the Interface Number
            if device["interface_number"] == 0:
                self.hid_device = hid.Device(path=device["path"])
                return True

        return False

    def set_led_brightness(self, brightness):
        # OneXFly brightness range is: 0 - 4 range, 0 is off, convert from 0 - 100 % range
        brightness = round(brightness / 20)

        # Check if device is available
        if self.hid_device is None:
            return False

        # Define the HID message for setting brightness.
        msg = [0x00, 0x07, 0xFF, 0xFD, 0x01, 0x05, brightness]

        # Write the HID message to set the LED brightness.
        self.hid_device.write(msg)

        return True

    def set_led_color(
        self,
        main_color: Color,
        secondary_color: Color,
        level: LEDLevel,
        speed: int = 100,
    ) -> bool:
        if not self.is_ready():
            return False

        prefix = [0x00, 0x07, 0xFF]
        LEDOption = [0x00]
        rgbData = [0x00]

        if level == LEDLevel.SolidColor:
            led_color = self.find_closest_color(main_color)
            LEDOption = [0xFE]
            rgbData = list(repeat([led_color.R, led_color.G, led_color.B], 20))

        elif level == LEDLevel.Rainbow:
            LEDOption = [0x03]
            rgbData = list(repeat(0x00, 60))

        else:
            return False

        msg = prefix + LEDOption + rgbData + [0x00]

        self.hid_device.write(msg)

        return True

    @staticmethod
    def find_closest_color(input_color: Color) -> Color:
        predefined_colors = [
            Color(255, 0, 0),
            Color(255, 82, 0),
            Color(255, 255, 0),
            Color(130, 255, 0),
            Color(0, 255, 0),
            Color(0, 255, 110),
            Color(0, 255, 255),
            Color(130, 255, 255),
            Color(0, 0, 255),
            Color(122, 0, 255),
            Color(255, 0, 255),
            Color(255, 0, 129),
        ]

        closest_color = predefined_colors[0]
        min_distance = OneXLEDDevice.calculate_distance(input_color, closest_color)

        # Iterate through predefined colors to find the closest one
        for predefined_color in predefined_colors:
            distance = OneXLEDDevice.calculate_distance(input_color, predefined_color)
            if distance < min_distance:
                min_distance = distance
                closest_color = predefined_color

        return closest_color

    @staticmethod
    def calculate_distance(color1: Color, color2: Color) -> float:
        deltaR = color2.R - color1.R
        deltaG = color2.G - color1.G
        deltaB = color2.B - color1.B

        return sqrt(deltaR * deltaR + deltaG * deltaG + deltaB * deltaB)
