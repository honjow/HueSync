from itertools import repeat, chain
from utils import Color, LEDLevel
from config import logger
import serial
import time


class OneXLEDDeviceSerial:
    def __init__(self):
        self.ser = None

    def is_ready(self) -> bool:
        # ser = serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0', baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_EVEN, stopbits = serial.STOPBITS_TWO)
        ser = serial.Serial(
            "/dev/ttyUSB0",
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
        )

        if ser.isOpen():
            self.ser = ser
            return True
        else:
            try:
                self.ser = ser
                self.ser.open()
                return True
            except Exception as e:
                logger.error(f"Error opening serial port: {e}")
                return False

    def set_led_brightness(self, brightness: int) -> bool:

        if not self.is_ready():
            return False

        prefix = [0xFD, 0x3F, 0x00]
        dataPrefix = [0x03, 0x00, 0x01, 0x05]
        # brightness level 0,1,3,4 (0x00, 0x01, 0x03, 0x04)
        data = [0x04]
        suffix = [0x3F, 0xFD]

        fillData = list(repeat([0x00], 54))

        brightness_data = list(chain(prefix, dataPrefix, data, fillData, suffix))
        bytes_data = bytes(bytearray(brightness_data))

        hex_data = " ".join([f"{x:02X}" for x in brightness_data])
        logger.info(f"hex_data={hex_data}")

        self.ser.write(bytes_data)
        return True

    def set_led_color(
        self,
        main_color: Color,
        level: LEDLevel,
        speed: int = 100,
    ) -> bool:
        if not self.is_ready():
            return False

        prefix = [0xFD, 0x3F]

        leftLed = [0x03]
        rightLed = [0x04]

        LEDOption = [0xFE]
        dataPrefix = [0x00, 0x00]
        rgbData = [0x00]

        suffix = [0x3F, 0xFD]

        if level == LEDLevel.SolidColor:
            led_color = main_color
            LEDOption = [0xFE]
            rgbData = list(repeat([led_color.R, led_color.G, led_color.B], 18))

        elif level == LEDLevel.Rainbow:
            LEDOption = [0x03]
            rgbData = list(repeat(0x00, 54))

        else:
            return False

        left_msg = list(chain(prefix, leftLed, LEDOption, dataPrefix, rgbData, suffix))
        right_msg = list(
            chain(prefix, rightLed, LEDOption, dataPrefix, rgbData, suffix)
        )

        left_msg_hex = " ".join([f"{x:02X}" for x in left_msg])
        right_msg_hex = " ".join([f"{x:02X}" for x in right_msg])

        logger.info(f"left_msg hex_data={left_msg_hex}")
        logger.info(f"right_msg hex_data={right_msg_hex}")

        l_bytes = bytes(bytearray(left_msg))
        r_bytes = bytes(bytearray(right_msg))

        self.ser.write(l_bytes)
        time.sleep(0.2)
        self.ser.write(r_bytes)

        return True
