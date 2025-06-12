import time

from config import DEFAULT_BRIGHTNESS, logger
from ec import EC
from led.ayaneo_led_device_ec import AyaNeoLEDDeviceEC
from utils import AyaJoystickGroup, AyaLedZone, Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class AyaNeoLEDDevice(BaseLEDDevice):
    """
    AyaNeoLEDDevice offers advanced control for AyaNeo devices, supporting pixel-level
    adjustments and various modes.

    AyaNeoLEDDevice为AyaNeo设备提供高级控制，支持像素级调整和各种模式。
    """

    def __init__(self):
        super().__init__()
        self.aya_led_device_ec = AyaNeoLEDDeviceEC()

    def _set_solid_color(self, color: Color) -> None:
        # self.set_color_all(color)
        self.aya_led_device_ec.set_led_color(color)

    def get_suspend_mode(self) -> str:
        return self.aya_led_device_ec.get_suspend_mode()

    def set_suspend_mode(self, mode: str) -> None:
        self.aya_led_device_ec.set_suspend_mode(mode)

    def suspend(self) -> None:
        self.aya_led_device_ec.suspend()

    def resume(self) -> None:
        self.aya_led_device_ec.resume()

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

        self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Right.value, color)
        self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Bottom.value, color)
        self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Left.value, color)
        self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Top.value, color)

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
        return capabilities
