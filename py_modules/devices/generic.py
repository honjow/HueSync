from config import logger
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice
from .sysfs_led_mixin import SysfsLEDMixin


class GenericLEDDevice(SysfsLEDMixin, BaseLEDDevice):
    """
    GenericLEDDevice serves as a base class for LED devices, providing basic functionality
    for setting color and brightness via sysfs.

    GenericLEDDevice作为LED设备的基类，通过 sysfs 提供设置颜色和亮度的基本功能。
    """

    def __init__(self):
        super().__init__()
        # Detect sysfs LED path on initialization
        # 初始化时检测 sysfs LED 路径
        self._detect_sysfs_led_path()

    def _set_solid_color(self, color: Color) -> None:
        """
        Set solid color LED via sysfs
        通过 sysfs 设置纯色LED
        """
        logger.debug(f">>>> Setting color to {color}")
        self._set_color_by_sysfs(color)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        获取每个支持的模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        capabilities = super().get_mode_capabilities()
        # Add software effect support | 添加软件效果支持
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
        capabilities[RGBMode.Gradient] = RGBModeCapabilities(
            mode=RGBMode.Gradient,
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
