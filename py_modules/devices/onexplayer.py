import time

from config import PRODUCT_NAME, logger
from led.onex_led_device_hid import (
    X1_MINI_PAGE,
    X1_MINI_PID,
    X1_MINI_USAGE,
    X1_MINI_VID,
    XFLY_PAGE,
    XFLY_PID,
    XFLY_USAGE,
    XFLY_VID,
    OneXLEDDeviceHID,
)
from led.onex_led_device_serial import OneXLEDDeviceSerial
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class OneXLEDDevice(BaseLEDDevice):
    """
    OneXLEDDevice is designed for OneX devices, enabling HID and serial communication
    for color and mode settings.

    OneXLEDDevice专为OneX设备设计，支持HID和串行通信以进行颜色和模式设置。
    """

    def __init__(self):
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Solid

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [
            RGBMode.Disabled,
            RGBMode.Solid,
            RGBMode.Rainbow,
        ]

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for Asus devices.
        获取 Asus 设备每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping RGB modes to their capabilities.
        """
        capabilities = super().get_mode_capabilities()
        capabilities[RGBMode.Rainbow] = RGBModeCapabilities(
            mode=RGBMode.Rainbow,
            color=False,
            color2=False,
            speed=True,
        )
        capabilities[RGBMode.Battery] = RGBModeCapabilities(
            mode=RGBMode.Battery,
            color=False,
            color2=False,
            speed=False,
            brightness=True,
        )
        return capabilities

    def _set_hardware_color(
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
                retry_delay *= 2  # Exponential backoff | 指数退避

            ledDevice = OneXLEDDeviceHID(
                [XFLY_VID, X1_MINI_VID],
                [XFLY_PID, X1_MINI_PID],
                [XFLY_PAGE, X1_MINI_PAGE],
                [XFLY_USAGE, X1_MINI_USAGE],
            )
            if ledDevice.is_ready():
                logger.info(f"set_onex_color: color={color}")
                # ledDevice.set_led_color(color, RGBMode.Solid)
                ledDevice.set_led_color_new(color, RGBMode.Solid)
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
