from config import (
    PRODUCT_NAME,
    logger,
)
from id_info import ID_MAP
from led.ausu_led_device_hid import AsusLEDDeviceHID
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class AsusLEDDevice(BaseLEDDevice):
    """
    AsusLEDDevice provides control for Asus devices, integrating with specific
    product IDs for tailored settings.

    AsusLEDDevice为Asus设备提供控制，集成特定产品ID以进行定制设置。
    """

    def __init__(self):
        super().__init__()
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                self.id_info = id_info

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        try:
            ledDevice = AsusLEDDeviceHID(
                self.id_info.vid, self.id_info.pid, [0xFF31], [0x0080]
            )
            if ledDevice.is_ready():
                init = self._current_mode != mode
                logger.info(f"set_asus_color: color={color} mode={mode} init={init}")
                if mode:
                    ledDevice.set_led_color(color, mode, init=init)
                    self._current_mode = mode
                return
            logger.info("set_asus_color: device not ready")
        except Exception as e:
            logger.error(e, exc_info=True)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for Asus devices.
        获取 Asus 设备每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping RGB modes to their capabilities.
        """
        return {
            RGBMode.Disabled: RGBModeCapabilities(
                mode=RGBMode.Disabled,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                supports_color=False,
                supports_color2=False,
                supports_speed=True,
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                supports_color=True,
                supports_color2=False,
                supports_speed=True,
            ),
            # RGBMode.Duality: RGBModeCapabilities(
            #     mode=RGBMode.Duality,
            #     supports_color=True,
            #     supports_color2=True,
            #     supports_speed=True,
            # ),
        }
