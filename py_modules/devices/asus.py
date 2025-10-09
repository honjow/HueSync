from config import PRODUCT_NAME, logger
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
        self._current_real_mode: RGBMode = RGBMode.Disabled
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                self.id_info = id_info

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [
            RGBMode.Disabled,
            RGBMode.Solid,
            RGBMode.Pulse,
            RGBMode.Duality,
            RGBMode.Rainbow,
            RGBMode.Spiral,
        ]

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
        brightness_level: str | None = None,
    ) -> None:
        if not color:
            return

        try:
            ledDevice = AsusLEDDeviceHID(
                vid=[self.id_info.vid],
                pid=[self.id_info.pid],
                usage_page=[0xFF31],
                usage=[0x0080],
            )
            if ledDevice.is_ready():
                init = self._current_real_mode != mode or init
                logger.debug(
                    f"set_asus_color: mode={mode} color={color} secondary={color2} init={init} speed={speed}"
                )
                if mode:
                    if init:
                        ledDevice.set_led_color(color, RGBMode.Disabled, init=True)
                    ledDevice.set_led_color(
                        color, mode, init=init, secondary_color=color2, speed=speed or "low"
                    )
                self._current_real_mode = mode or RGBMode.Disabled
                return
            logger.info("set_asus_color: device not ready")
        except Exception as e:
            logger.error(e, exc_info=True)
            raise

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
                color=False,
                color2=False,
                speed=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                color=True,
                color2=False,
                speed=False,
            ),
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                color=False,
                color2=False,
                speed=True,
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                color=True,
                color2=False,
                speed=True,
            ),
            RGBMode.Duality: RGBModeCapabilities(
                mode=RGBMode.Duality,
                color=True,
                color2=True,
                speed=True,
            ),
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                color=False,
                color2=False,
                speed=True,
            ),
            RGBMode.Battery: RGBModeCapabilities(
                mode=RGBMode.Battery,
                color=False,
                color2=False,
                speed=False,
                brightness=True,
            ),
        }
