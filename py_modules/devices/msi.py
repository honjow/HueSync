import time

from config import PRODUCT_NAME, logger
from id_info import ID_MAP
from led.msi_led_device_hid import MsiLEDDeviceHID
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class MsiLEDDevice(BaseLEDDevice):
    def __init__(self):
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Disabled
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                self.id_info = id_info

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [
            RGBMode.Disabled,
            RGBMode.Solid,
        ]

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
    ) -> None:
        if not color:
            return
        self._set_msi_color_hid(color)

    def _set_msi_color_hid(self, color: Color) -> None:
        max_retries = 3
        retry_delay = 1  # seconds
        for retry in range(max_retries + 1):
            if retry > 0:
                logger.info(f"Retry attempt {retry}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避

            ledDevice = MsiLEDDeviceHID(self.id_info.vid, self.id_info.pid)
            if ledDevice.is_ready():
                logger.info(f"set_msi_color: color={color}")
                ledDevice.set_led_color(color, RGBMode.Solid)
                return
            logger.info("set_msi_hid: device not ready")

        logger.warning("Failed to set color after all retries")

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        获取每个支持的模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        capabilities = super().get_mode_capabilities()
        # 添加软件效果支持
        capabilities[RGBMode.Pulse] = RGBModeCapabilities(
            mode=RGBMode.Pulse,
            color=True,
            color2=False,
            speed=True,
        )
        capabilities[RGBMode.Rainbow] = RGBModeCapabilities(
            mode=RGBMode.Rainbow,
            color=False,
            color2=False,
            speed=True,
        )
        capabilities[RGBMode.Duality] = RGBModeCapabilities(
            mode=RGBMode.Duality,
            color=True,
            color2=True,
            speed=True,
        )
        capabilities[RGBMode.Battery] = RGBModeCapabilities(
            mode=RGBMode.Battery,
            color=True,
            color2=False,
            speed=False,
            brightness=True,
        )
        return capabilities
