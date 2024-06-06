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
        dataPrefix = [0x03, 0x00, 0x01, 0x05]
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
        return True

    def set_led_color(
        self,
        main_color: Color,
        level: LEDLevel,
    ) -> bool:
        if not self.is_ready():
            return False

        dataLength = 64

        prefix = [0xFD, 0x3F]

        leftLed = [0x03]
        rightLed = [0x04]

        LEDOption = [0xFE]
        dataPrefix = [0x00, 0x00]
        rgbData = [0x00]

        suffix = [0x3F, 0xFD]

        rgbDataLen = (
            dataLength
            - len(prefix)
            - len(leftLed)
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

        left_msg = list(
            chain(prefix, leftLed, LEDOption, dataPrefix, chain(*rgbData), suffix)
        )
        right_msg = list(
            chain(prefix, rightLed, LEDOption, dataPrefix, chain(*rgbData), suffix)
        )

        left_msg_hex = " ".join([f"{x:02X}" for x in left_msg])
        right_msg_hex = " ".join([f"{x:02X}" for x in right_msg])

        logger.info(f"left_msg len={len(left_msg)} hex_data={left_msg_hex}")
        logger.info(f"right_msg len={len(right_msg)} hex_data={right_msg_hex}")

        l_bytes = bytes(bytearray(left_msg))
        r_bytes = bytes(bytearray(right_msg))

        self.ser.write(l_bytes)
        time.sleep(0.2)
        self.ser.write(r_bytes)

        return True
