import time

from config import PRODUCT_NAME, logger
from led.onex_led_device_hid import OneXLEDDeviceHID
from led.onex_led_device_serial import OneXLEDDeviceSerial
from utils import Color, RGBMode

from .led_device import BaseLEDDevice


class OneXLEDDevice(BaseLEDDevice):
    """
    OneXLEDDevice is designed for OneX devices, enabling HID and serial communication
    for color and mode settings.

    OneXLEDDevice专为OneX设备设计，支持HID和串行通信以进行颜色和模式设置。
    """

    def _set_solid_color(self, color: Color) -> None:
        self._set_color(RGBMode.Solid, color)

    def _set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
    ) -> None:
        if not color:
            return
        if "ONEXPLAYER X1" in PRODUCT_NAME:
            self.set_onex_color_serial(color)
        else:
            self.set_onex_color_hid(color)

    def set_onex_color_hid(self, color: Color) -> None:
        max_retries = 3
        retry_delay = 1  # seconds
        for retry in range(max_retries + 1):
            if retry > 0:
                logger.info(f"Retry attempt {retry}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避

            ledDevice = OneXLEDDeviceHID(0x1A2C, 0xB001)
            if ledDevice.is_ready():
                logger.info(f"set_onex_color: color={color}")
                ledDevice.set_led_color(color, RGBMode.Solid)
                return
            logger.info("set_onex_color_hid: device not ready")

        logger.warning("Failed to set color after all retries")

    def set_onex_color_serial(self, color: Color) -> None:
        try:
            ledDevice = OneXLEDDeviceSerial()
            if ledDevice.is_ready():
                logger.info(f"set_onex_color: color={color}")
                ledDevice.set_led_color(color, RGBMode.Solid)
        except Exception as e:
            logger.error(e, exc_info=True)
