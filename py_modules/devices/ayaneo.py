import time

from config import DEFAULT_BRIGHTNESS, IS_AYANEO_EC_SUPPORTED, logger
from ec import EC
from utils import AyaJoystickGroup, AyaLedZone, Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class AyaNeoLEDDevice(BaseLEDDevice):
    """
    AyaNeoLEDDevice offers advanced control for AyaNeo devices, supporting pixel-level
    adjustments and various modes.

    AyaNeoLEDDevice为AyaNeo设备提供高级控制，支持像素级调整和各种模式。
    """

    def _set_solid_color(self, color: Color) -> None:
        self.set_color_all(color)

    def set_color_one(self, group: int, ledZone: int, color: Color) -> None:
        self.set_aya_subpixel(group, ledZone * 3, color.R)
        self.set_aya_subpixel(group, ledZone * 3 + 1, color.G)
        self.set_aya_subpixel(group, ledZone * 3 + 2, color.B)

    def set_aya_subpixel(self, group: int, subpixel_idx: int, brightness: int) -> None:
        logger.debug(
            f"group={group} subpixel_idx={subpixel_idx},brightness={brightness}"
        )
        self.aya_ec_cmd(group, subpixel_idx, brightness)

    def aya_ec_cmd(self, group: int, command: int, argument: int) -> None:
        for x in range(2):
            EC.Write(0x6D, group)
            EC.Write(0xB1, command)
            EC.Write(0xB2, argument)
            EC.Write(0xBF, 0x10)
            time.sleep(0.005)
            # EC.Write(0xBF, 0xFF)
            EC.Write(0xBF, 0xFE)

    def set_color_all(self, color: Color) -> None:
        color = Color(
            color.R * DEFAULT_BRIGHTNESS // 100,
            color.G * DEFAULT_BRIGHTNESS // 100,
            color.B * DEFAULT_BRIGHTNESS // 100,
        )

        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Right, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Bottom, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Left, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Top, color)

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
            supports_color=True,
            supports_color2=False,
            supports_speed=True,
        )
        capabilities[RGBMode.Rainbow] = RGBModeCapabilities(
            mode=RGBMode.Rainbow,
            supports_color=False,
            supports_color2=False,
            supports_speed=True,
        )
        capabilities[RGBMode.Duality] = RGBModeCapabilities(
            mode=RGBMode.Duality,
            supports_color=True,
            supports_color2=True,
            supports_speed=True,
        )
        return capabilities
