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
        self._custom_zone_initialized = False  # Track if custom zones have been initialized

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
                
                # Send initial config_rgb to ensure RGB hardware is enabled
                # 发送初始 config_rgb 命令以确保 RGB 硬件已启用
                # This is critical after Windows has disabled RGB (e.g., dual-boot scenario)
                # 这在 Windows 禁用 RGB 后至关重要（例如双启动场景）
                try:
                    from led.asus_led_device_hid import config_rgb
                    device.hid_device.write(config_rgb(
                        boot=device.rgb_boot,
                        charging=device.rgb_charging
                    ))
                    logger.info("Sent initial config_rgb to enable RGB hardware")
                except Exception as e:
                    logger.warning(f"Failed to send initial config_rgb: {e}")
                
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
        
        # Detect Xbox Ally variant
        # 检测 Xbox Ally 变体
        from config import PRODUCT_NAME
        product_upper = PRODUCT_NAME.upper()
        
        if "XBOX ALLY" in product_upper:
            base_caps["variant"] = "xbox"
            logger.info("Detected Xbox Ally variant")
        else:
            base_caps["variant"] = "standard"
            logger.info("Detected standard Ally variant")
        
        return base_caps

    def supports_custom_rgb(self) -> bool:
        """
        Check if device supports custom RGB animations.
        检查设备是否支持自定义 RGB 动画。
        """
        return self._get_or_create_ally_device() is not None

    def set_custom_zone_colors(
        self, 
        left_colors: list[list[int]], 
        right_colors: list[list[int]]
    ) -> bool:
        """
        Set static custom colors for LED zones (unified API).
        为 LED 区域设置静态自定义颜色（统一 API）。
        
        Args:
            left_colors: List of RGB colors for left zones (2 zones)
                        左侧区域的 RGB 颜色列表（2个区域）
            right_colors: List of RGB colors for right zones (2 zones)
                         右侧区域的 RGB 颜色列表（2个区域）
        
        Returns:
            bool: True if successful
                  bool：成功返回 True
        """
        # Combine colors for 4-zone format
        # 合并颜色为 4 区域格式
        all_colors = [(r, g, b) for r, g, b in left_colors + right_colors]
        
        # Priority 1: Try sysfs interface (faster and more stable)
        # 优先级 1：尝试 sysfs 接口（更快更稳定）
        if self._sysfs_led_path and self._set_zone_colors_by_sysfs(all_colors):
            self._custom_zone_initialized = True
            return True
        
        # Priority 2: Fallback to HID interface for compatibility
        # 优先级 2：降级到 HID 接口以保持兼容性
        logger.debug("sysfs not available or failed, using HID interface")
        device = self._get_or_create_ally_device()
        if not device:
            logger.error("Ally HID device not available for custom zone colors")
            return False
        
        # Send init commands only on first call to avoid flicker
        # 只在首次调用时发送初始化命令以避免闪烁
        init = not self._custom_zone_initialized
        result = device.set_custom_zone_colors(all_colors, init=init)
        if result:
            self._custom_zone_initialized = True
        else:
            # If write failed, device may be invalid - clear cached device
            # 如果写入失败，设备可能已失效 - 清除缓存的设备
            logger.warning("Failed to set zone colors via HID, clearing device cache")
            self._ally_hid_device = None
            self._custom_zone_initialized = False
        return result


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

    def _set_zone_colors_by_sysfs(self, colors: list[tuple[int, int, int]]) -> bool:
        """
        Set different colors for 4 LED zones via sysfs interface.
        通过 sysfs 接口为 4 个 LED 区域设置不同颜色。
        
        This method is optimized for animation engines - faster and more stable than HID.
        此方法为动画引擎优化 - 比 HID 更快更稳定。
        
        Args:
            colors: List of 4 RGB tuples, one for each zone
                    4 个 RGB 元组列表，每个区域一个
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._sysfs_led_path:
            return False
        
        if len(colors) != 4:
            logger.error(f"Expected 4 colors for Ally zones, got {len(colors)}")
            return False
        
        try:
            multi_index_path = os.path.join(self._sysfs_led_path, "multi_index")
            if not os.path.exists(multi_index_path):
                return False
            
            with open(multi_index_path, "r") as f:
                multi_index = f.read().strip()
                count = len(multi_index.split(" "))
                
                multi_intensity_path = os.path.join(self._sysfs_led_path, "multi_intensity")
                with open(multi_intensity_path, "w") as f:
                    if count == 12:
                        # 4 zones × RGB (decimal format) | 4 区域 × RGB（十进制格式）
                        # Format: "R1 G1 B1 R2 G2 B2 R3 G3 B3 R4 G4 B4"
                        color_str = " ".join([f"{r} {g} {b}" for r, g, b in colors])
                        f.write(color_str)
                        logger.debug(f"Set zone colors via sysfs (decimal): {color_str}")
                    elif count == 4:
                        # 4 zones (hex format) | 4 区域（十六进制格式）
                        # Format: "0xRRGGBB 0xRRGGBB 0xRRGGBB 0xRRGGBB"
                        hex_colors = " ".join([f"0x{r:02x}{g:02x}{b:02x}" for r, g, b in colors])
                        f.write(hex_colors)
                        logger.debug(f"Set zone colors via sysfs (hex): {hex_colors}")
                    else:
                        logger.warning(f"Unexpected multi_index count: {count}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set zone colors via sysfs: {e}")
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

    def suspend(self) -> None:
        """
        Handle suspend event (before sleep).
        处理挂起事件（睡眠前）。
        """
        # Currently no special handling needed for suspend
        # 当前挂起时无需特殊处理
        pass

    def resume(self) -> None:
        """
        Handle resume event (after wakeup).
        处理恢复事件（唤醒后）。
        
        Re-disables dynamic lighting on Xbox Ally X after system wakeup,
        as Windows driver may have re-enabled it.
        在系统唤醒后重新禁用 Xbox Ally X 的动态灯光，
        因为 Windows 驱动可能已重新启用它。
        """
        logger.info("Resume event: Re-disabling dynamic lighting for Xbox Ally")
        
        # Re-disable dynamic lighting if HID device exists
        # 如果 HID 设备存在，重新禁用动态灯光
        if self._ally_hid_device:
            try:
                result = self._ally_hid_device.re_disable_dynamic_lighting()
                if result:
                    logger.info("Successfully re-disabled dynamic lighting after wakeup")
                else:
                    logger.warning("Failed to re-disable dynamic lighting after wakeup")
            except Exception as e:
                logger.error(f"Error re-disabling dynamic lighting on resume: {e}", exc_info=True)
