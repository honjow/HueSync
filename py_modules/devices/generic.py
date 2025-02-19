import os

from config import DEFAULT_BRIGHTNESS, LED_PATH, logger
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class GenericLEDDevice(BaseLEDDevice):
    """
    GenericLEDDevice serves as a base class for LED devices, providing basic functionality
    for setting color and brightness.

    GenericLEDDevice作为LED设备的基类，提供设置颜色和亮度的基本功能。
    """

    def _set_solid_color(self, color: Color) -> None:
        """实际设置颜色的方法"""
        if os.path.exists(LED_PATH):
            logger.debug(f">>>> Setting color to {color}")
            with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                _brightness: int = DEFAULT_BRIGHTNESS * 255 // 100
                logger.debug(f"brightness={_brightness}")
                f.write(str(_brightness))
            with open(os.path.join(LED_PATH, "multi_intensity"), "w") as f:
                f.write(f"{color.R} {color.G} {color.B}")

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
