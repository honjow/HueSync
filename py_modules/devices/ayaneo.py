import time

from config import DEFAULT_BRIGHTNESS, logger
from ec import EC
from led.ayaneo_led_device_ec import AyaNeoLEDDeviceEC
from utils import AyaJoystickGroup, AyaLedZone, Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice
from .sysfs_led_mixin import SysfsLEDMixin


class AyaNeoLEDDevice(SysfsLEDMixin, BaseLEDDevice):
    """
    AyaNeoLEDDevice offers advanced control for AyaNeo devices, supporting pixel-level
    adjustments and various modes via EC control. Falls back to sysfs if available.

    AyaNeoLEDDevice为AyaNeo设备提供高级控制，通过 EC 控制支持像素级调整和各种模式。
    如可用，回退到 sysfs。
    """

    # Define sysfs search keywords for AyaNeo devices with kernel patches
    # 为带有内核补丁的 AyaNeo 设备定义 sysfs 搜索关键词
    SYSFS_LED_PATHS = ["ayaneo", "multicolor"]

    def __init__(self):
        super().__init__()
        self.aya_led_device_ec = AyaNeoLEDDeviceEC()
        # Detect sysfs LED path (may or may not exist depending on kernel patches)
        # 检测 sysfs LED 路径（取决于内核补丁可能存在或不存在）
        self._detect_sysfs_led_path()

    def _set_solid_color(self, color: Color) -> None:
        """
        Set solid color, prioritizing sysfs (if available), falling back to EC control.
        设置纯色，优先使用 sysfs（如可用），回退到 EC 控制。
        
        For solid color mode, prefer sysfs kernel driver (more stable and standard).
        EC control is reserved for advanced features like custom RGB.
        对于纯色模式，优先使用 sysfs 内核驱动（更稳定和标准）。
        EC 控制保留给高级功能，如自定义 RGB。
        """
        # Try sysfs first if available (preferred for solid colors)
        # 如可用，首先尝试 sysfs（纯色首选）
        if self._has_sysfs_support():
            if self._set_color_by_sysfs(color):
                logger.debug("Set solid color via sysfs")
                return
            else:
                logger.warning("sysfs control failed, trying EC fallback")
        
        # Fallback to EC control
        # 回退到 EC 控制
        try:
            self.aya_led_device_ec.set_led_color(color)
            logger.debug("Set solid color via EC")
        except Exception as e:
            logger.error(f"Both sysfs and EC control failed: {e}")
            raise

    def set_custom_zone_colors(self, left_colors, right_colors, button_color=None):
        """
        Set custom colors for individual LED zones (for custom RGB animations)
        为每个 LED 区域设置自定义颜色（用于自定义 RGB 动画）
        
        Delegates to AyaNeoLEDDeviceEC for zone-level control via EC.
        委托给 AyaNeoLEDDeviceEC 通过 EC 进行区域级控制。
        
        Args:
            left_colors: List of 4 RGB colors for left grip zones
                         左手柄 4 个区域的 RGB 颜色列表
            right_colors: List of 4 RGB colors for right grip zones
                          右手柄 4 个区域的 RGB 颜色列表
            button_color: Optional RGB color for button zone (KUN only)
                          按钮区域的 RGB 颜色（仅 KUN 设备）
        """
        return self.aya_led_device_ec.set_custom_zone_colors(left_colors, right_colors, button_color)

    def get_suspend_mode(self) -> str:
        return self.aya_led_device_ec.get_suspend_mode()

    def set_suspend_mode(self, mode: str) -> None:
        self.aya_led_device_ec.set_suspend_mode(mode)

    def suspend(self) -> None:
        self.aya_led_device_ec.suspend()

    def resume(self) -> None:
        self.aya_led_device_ec.resume()

    # def set_color_one(self, group: int, ledZone: int, color: Color) -> None:
    #     self.set_aya_subpixel(group, ledZone * 3, color.R)
    #     self.set_aya_subpixel(group, ledZone * 3 + 1, color.G)
    #     self.set_aya_subpixel(group, ledZone * 3 + 2, color.B)

    # def set_aya_subpixel(self, group: int, subpixel_idx: int, brightness: int) -> None:
    #     logger.debug(
    #         f"group={group} subpixel_idx={subpixel_idx},brightness={brightness}"
    #     )
    #     self.aya_ec_cmd(group, subpixel_idx, brightness)

    # def aya_ec_cmd(self, group: int, command: int, argument: int) -> None:
    #     for x in range(2):
    #         EC.Write(0x6D, group)
    #         EC.Write(0xB1, command)
    #         EC.Write(0xB2, argument)
    #         EC.Write(0xBF, 0x10)
    #         time.sleep(0.005)
    #         # EC.Write(0xBF, 0xFF)
    #         EC.Write(0xBF, 0xFE)

    # def set_color_all(self, color: Color) -> None:
    #     color = Color(
    #         color.R * DEFAULT_BRIGHTNESS // 100,
    #         color.G * DEFAULT_BRIGHTNESS // 100,
    #         color.B * DEFAULT_BRIGHTNESS // 100,
    #     )

    #     self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Right.value, color)
    #     self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Bottom.value, color)
    #     self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Left.value, color)
    #     self.set_color_one(AyaJoystickGroup.ALL.value, AyaLedZone.Top.value, color)

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
        return capabilities

    def get_device_capabilities(self) -> dict:
        """
        Get device-specific capabilities including custom RGB support.
        获取设备特定功能，包括自定义 RGB 支持。

        Returns:
            dict: Device capabilities including ayaneo_custom_rgb support
        """
        base_caps = super().get_device_capabilities()
        # AyaNeo supports custom RGB configuration via software animation
        # 支持通过软件动画实现自定义 RGB 配置
        base_caps["custom_rgb"] = True
        return base_caps
