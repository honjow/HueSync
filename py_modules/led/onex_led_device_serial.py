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

        dataLength = 64

        prefix = [0xFD, 0x3F, 0x00]
        dataPrefix = [0xfd, 0x03, 0x00, 0x01, 0x05]
        # brightness level 0,1,3,4 (0x00, 0x01, 0x03, 0x04)
        data = [0x04]
        suffix = [0x3F, 0xFD]

        fillDataLength = (
            dataLength - len(prefix) - len(dataPrefix) - len(data) - len(suffix)
        )

        fillData = list(repeat([0x00], fillDataLength))

        brightness_data = list(
            chain(prefix, dataPrefix, data, chain(*fillData), suffix)
        )
        bytes_data = bytes(bytearray(brightness_data))

        hex_data = " ".join([f"{x:02X}" for x in brightness_data])
        logger.info(f"brightness len={len(brightness_data)} hex_data={hex_data}")

        self.ser.write(bytes_data)
        time.sleep(0.1)
        return True

    def set_led_color(self, main_color: Color, level: LEDLevel) -> bool:
        controlerLed = 0x00
        leftLed = 0x03
        rightLed = 0x04

        self.set_one_led_color(main_color, level, controlerLed)
        time.sleep(0.2)
        self.set_one_led_color(main_color, level, leftLed)
        time.sleep(0.2)
        self.set_one_led_color(main_color, level, rightLed)
        time.sleep(0.1)
        return True

    def set_one_led_color(
        self,
        main_color: Color,
        level: LEDLevel,
        ledPosition: int,
    ) -> bool:
        if not self.is_ready():
            return False

        dataLength = 64

        prefix = [0xFD, 0x3F]

        LEDOption = [0xFE]
        dataPrefix = [0x00, 0x00]
        rgbData = [0x00]

        suffix = [0x3F, 0xFD]

        rgbDataLen = (
            dataLength
            - len(prefix)
            - 1
            - len(LEDOption)
            - len(dataPrefix)
            - len(suffix)
        )

        if level == LEDLevel.SolidColor:
            led_color = main_color
            LEDOption = [0xFE]

            _rgbData = list(repeat([led_color.R, led_color.G, led_color.B], 20))
            rgbData = list(chain(*_rgbData))[:rgbDataLen]

        elif level == LEDLevel.Rainbow:
            LEDOption = [0x03]
            rgbData = list(repeat(0x00, rgbDataLen))
        else:
            return False

        msg = list(chain(prefix, [ledPosition], LEDOption, dataPrefix, rgbData, suffix))

        msg_hex = " ".join([f"{x:02X}" for x in msg])
        
        msg_bytes = bytes(bytearray(msg))

        logger.info(f"write msg, len={len(msg)} hex_data={msg_hex}")
        self.ser.write(msg_bytes)
        

        return True
