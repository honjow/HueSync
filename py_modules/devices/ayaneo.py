import time

from config import DEFAULT_BRIGHTNESS, USE_SYSFS_LED_CONTROL, logger
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
        
        # Cache multi-zone support status
        # 缓存多区域支持状态
        self._num_zones = None
        self._sysfs_multi_zone_available = False
        
        if self._has_sysfs_support():
            self._num_zones = self._detect_sysfs_multi_zones()
            self._sysfs_multi_zone_available = self._has_sysfs_multi_zone_support()
            
            if self._sysfs_multi_zone_available:
                logger.info(f"AyaNeo device: sysfs multi-zone support available ({self._num_zones} zones)")
            else:
                logger.info("AyaNeo device: sysfs available (single zone only, multi-zone via EC)")
        else:
            logger.info("AyaNeo device: no sysfs support, using EC control only")

    def _set_solid_color(self, color: Color) -> None:
        """
        Set solid color, prioritizing sysfs (if available), falling back to EC control.
        设置纯色，优先使用 sysfs（如可用），回退到 EC 控制。
        
        For solid color mode, prefer sysfs kernel driver (more stable and standard).
        Works with both old and new kernel drivers.
        对于纯色模式，优先使用 sysfs 内核驱动（更稳定和标准）。
        兼容新旧内核驱动。
        """
        # Try sysfs first if available (works with both old and new kernel drivers)
        # 如可用，首先尝试 sysfs（兼容新旧内核驱动）
        if USE_SYSFS_LED_CONTROL and self._has_sysfs_support():
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
        
        Prioritizes sysfs (if multi_intensity_zones available), falls back to EC control.
        优先使用 sysfs（如果 multi_intensity_zones 可用），回退到 EC 控制。
        
        Behavior:
        - With new kernel driver (multi_intensity_zones): Uses fast sysfs interface
        - With old kernel driver: Automatically falls back to EC control
        - No kernel driver: Uses EC control
        
        行为：
        - 新内核驱动（multi_intensity_zones）：使用快速的 sysfs 接口
        - 旧内核驱动：自动回退到 EC 控制
        - 无内核驱动：使用 EC 控制
        
        Args:
            left_colors: List of 4 RGB colors for left grip zones
                         左手柄 4 个区域的 RGB 颜色列表
            right_colors: List of 4 RGB colors for right grip zones
                          右手柄 4 个区域的 RGB 颜色列表
            button_color: Optional RGB color for button zone (KUN only)
                          按钮区域的 RGB 颜色（仅 KUN 设备）
        """
        # Only try sysfs if we confirmed multi-zone support during init
        # 仅在初始化时确认了多区域支持时才尝试 sysfs
        if USE_SYSFS_LED_CONTROL and self._sysfs_multi_zone_available:
            try:
                # Build complete zone list (9 zones for AyaNeo kernel driver)
                # 构建完整的区域列表（对于 AyaNeo 内核驱动必须是 9 个区域）
                zone_colors = []
                
                # Zones 0-3: Left joystick
                for color in left_colors:
                    if isinstance(color, (list, tuple)):
                        zone_colors.append((color[0], color[1], color[2]))
                    else:
                        zone_colors.append((color.R, color.G, color.B))
                
                # Zones 4-7: Right joystick
                for color in right_colors:
                    if isinstance(color, (list, tuple)):
                        zone_colors.append((color[0], color[1], color[2]))
                    else:
                        zone_colors.append((color.R, color.G, color.B))
                
                # Zone 8: AyaSpace button (KUN) or dummy zone (other devices)
                if button_color:
                    if isinstance(button_color, (list, tuple)):
                        zone_colors.append((button_color[0], button_color[1], button_color[2]))
                    else:
                        zone_colors.append((button_color.R, button_color.G, button_color.B))
                else:
                    zone_colors.append((0, 0, 0))  # Fill with black for non-KUN devices
                
                # Attempt sysfs write
                if len(zone_colors) == 9 and self._set_zones_color_by_sysfs(zone_colors):
                    logger.debug("Set custom zone colors via sysfs (9 zones)")
                    return True
                else:
                    logger.debug("sysfs multi-zone write failed, falling back to EC")
                    
            except Exception as e:
                logger.warning(f"sysfs zone control exception: {e}, falling back to EC")
        
        # Fallback to EC control (always available)
        # 回退到 EC 控制（始终可用）
        logger.debug("Using EC control for custom zone colors")
        return self.aya_led_device_ec.set_custom_zone_colors(left_colors, right_colors, button_color)

    def get_suspend_mode(self) -> str:
        mode = self.aya_led_device_ec.get_suspend_mode()
        logger.debug(f"AyaNeoLEDDevice.get_suspend_mode() -> '{mode}'")
        return mode

    def set_suspend_mode(self, mode: str) -> None:
        logger.debug(f"AyaNeoLEDDevice.set_suspend_mode('{mode}')")
        self.aya_led_device_ec.set_suspend_mode(mode)

    def suspend(self) -> None:
        self.aya_led_device_ec.suspend()

    def resume(self) -> None:
        self.aya_led_device_ec.resume()

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
            color=False,
            color2=False,
            speed=False,
            brightness=True,
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
