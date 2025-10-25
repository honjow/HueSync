import os
from typing import Optional

from config import DEFAULT_BRIGHTNESS, logger
from led.asus_led_device_hid import AsusLEDDeviceHID
from utils import Color, RGBMode

from .asus import AsusLEDDevice
from .sysfs_led_mixin import SysfsLEDMixin


class AllyLEDDevice(SysfsLEDMixin, AsusLEDDevice):
    """
    AllyLEDDevice provides control functionalities specific to Ally LED devices,
    including color and mode adjustments, and custom RGB animations.

    AllyLEDDevice提供Ally LED设备特有的控制功能，包括颜色和模式调整，以及自定义RGB动画。
    """

    # Define sysfs LED path search keywords | 定义 sysfs LED 路径搜索关键词
    SYSFS_LED_PATHS = ["ally", "joystick_rings"]

    def __init__(self):
        super().__init__()
        # SysfsLEDMixin will auto-detect sysfs path | SysfsLEDMixin 会自动检测 sysfs 路径
        self._ally_hid_device: AsusLEDDeviceHID | None = None
        self._custom_rgb_capable = False

    def _get_or_create_ally_device(self) -> AsusLEDDeviceHID | None:
        """
        Get or create Ally-specific HID device for custom RGB control.
        获取或创建 Ally 专用 HID 设备用于自定义 RGB 控制。
        """
        if self._ally_hid_device and self._ally_hid_device.is_ready():
            return self._ally_hid_device
        
        try:
            device = AsusLEDDeviceHID(
                vid=[self.id_info.vid],
                pid=[self.id_info.pid],
                usage_page=[0xFF31],
                usage=[0x0080],
                num_zones=4,  # ROG Ally has 4 zones
            )
            if device.is_ready():
                logger.info("Created Ally HID device for custom RGB control")
                self._ally_hid_device = device
                self._custom_rgb_capable = True
                return device
        except Exception as e:
            logger.error(f"Failed to create Ally HID device: {e}", exc_info=True)
        
        return None

    def get_device_capabilities(self) -> dict:
        """
        Get device capabilities for ROG Ally.
        获取 ROG Ally 设备能力。
        
        Returns:
            dict: Device capabilities including custom RGB support
        """
        base_caps = super().get_device_capabilities()
        
        # ROG Ally supports custom RGB configuration via software animation
        # ROG Ally 通过软件动画支持自定义 RGB 配置
        base_caps["custom_rgb"] = True
        base_caps["device_type"] = "rog_ally"
        
        return base_caps

    def supports_custom_rgb(self) -> bool:
        """
        Check if device supports custom RGB animations.
        检查设备是否支持自定义 RGB 动画。
        """
        return self._get_or_create_ally_device() is not None

    def set_custom_zone_colors(self, colors: list[tuple[int, int, int]]) -> bool:
        """
        Set static custom colors for all LED zones.
        为所有 LED 区域设置静态自定义颜色。
        
        Args:
            colors: List of RGB tuples for each zone
                    每个区域的 RGB 元组列表
        
        Returns:
            bool: True if successful
                  bool：成功返回 True
        """
        device = self._get_or_create_ally_device()
        if not device:
            logger.error("Ally HID device not available for custom zone colors")
            return False
        
        return device.set_custom_zone_colors(colors)

    def start_custom_animation(
        self, 
        keyframes: list[list[tuple[int, int, int]]], 
        speed: int, 
        brightness: int
    ) -> bool:
        """
        Start custom RGB animation with keyframes.
        使用关键帧启动自定义 RGB 动画。
        
        Args:
            keyframes: List of keyframes
                       关键帧列表
            speed: Animation speed (1-20)
                   动画速度（1-20）
            brightness: Brightness level (0-100)
                        亮度级别（0-100）
        
        Returns:
            bool: True if started successfully
                  bool：成功启动返回 True
        """
        device = self._get_or_create_ally_device()
        if not device:
            logger.error("Ally HID device not available for custom animation")
            return False
        
        return device.start_custom_animation(keyframes, speed, brightness)

    def stop_custom_animation(self) -> None:
        """
        Stop the running custom RGB animation.
        停止正在运行的自定义 RGB 动画。
        """
        if self._ally_hid_device:
            self._ally_hid_device.stop_custom_animation()

    def is_custom_animation_running(self) -> bool:
        """
        Check if custom animation is currently running.
        检查自定义动画是否正在运行。
        """
        if not self._ally_hid_device:
            return False
        return self._ally_hid_device.is_custom_animation_running()

    def _set_color_by_sysfs(self, color: Color, brightness: Optional[int] = None) -> bool:
        """
        Set LED color via sysfs interface with Ally-specific 4 zone format.
        通过 sysfs 接口设置 LED 颜色，使用 Ally 专用的 4 zone 格式。
        
        Args:
            color: RGB color to set
            brightness: Brightness level (0-255), if None uses system default
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._sysfs_led_path:
            return False
        
        try:
            multi_index_path = os.path.join(self._sysfs_led_path, "multi_index")
            if os.path.exists(multi_index_path):
                with open(multi_index_path, "r") as f:
                    multi_index = f.read().strip()
                    count = len(multi_index.split(" "))
                    logger.debug(f"Ally multi_index count: {count}")
                    
                    multi_intensity_path = os.path.join(self._sysfs_led_path, "multi_intensity")
                    with open(multi_intensity_path, "w") as f:
                        if count == 12:
                            # 4 zones × RGB (decimal format) | 4 区域 × RGB（十进制格式）
                            colors = f"{color.R} {color.G} {color.B} " * 4
                            f.write(colors.strip())
                        elif count == 4:
                            # 4 zones (hex format) | 4 区域（十六进制格式）
                            color_hex = color.hex()
                            f.write(f"0x{color_hex} 0x{color_hex} 0x{color_hex} 0x{color_hex}")
            
            # Set brightness | 设置亮度
            brightness_path = os.path.join(self._sysfs_led_path, "brightness")
            if os.path.exists(brightness_path):
                if brightness is None:
                    brightness = DEFAULT_BRIGHTNESS * 255 // 100
                with open(brightness_path, "w") as f:
                    f.write(str(brightness))
                logger.debug(f"Set Ally brightness: {brightness}")
            
            logger.debug(f"Set Ally color via sysfs: RGB({color.R}, {color.G}, {color.B})")
            return True
            
        except Exception as e:
            logger.warning(f"Ally sysfs set color failed: {e}")
            return False

    def _set_solid_color(self, color: Color) -> None:
        """
        Set solid color with automatic fallback from sysfs to HID.
        设置单色，自动从 sysfs 降级到 HID。
        """
        # Try sysfs first | 首先尝试 sysfs
        if self._set_color_by_sysfs(color):
            return
        
        # Fallback to HID | 降级到 HID
        logger.debug("Ally sysfs unavailable or failed, using HID fallback")
        super()._set_hardware_color(RGBMode.Solid, color)

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
        **kwargs,  # Accept brightness_level and other future parameters
    ) -> None:
        if not color:
            return
        if mode == RGBMode.Solid:
            self._set_solid_color(color)
        else:
            super().set_color(
                mode=mode,
                color=color,
                color2=color2,
                init=init,
                brightness=brightness,
                speed=speed,
                **kwargs
            )
