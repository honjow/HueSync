import os
from typing import Optional

from config import LED_PATH, logger
from utils import Color


class SysfsLEDMixin:
    """
    Mixin for sysfs-based LED control
    提供基于 sysfs 的 LED 控制功能的 Mixin
    
    This mixin provides basic sysfs LED control functionality that can be shared
    across multiple device classes. It supports standard Linux LED subsystem paths
    and multi_intensity files for RGB control.
    
    该 Mixin 提供可在多个设备类之间共享的基本 sysfs LED 控制功能。
    它支持标准的 Linux LED 子系统路径和用于 RGB 控制的 multi_intensity 文件。
    
    Usage:
        class MyDevice(SysfsLEDMixin, BaseLEDDevice):
            SYSFS_LED_PATHS = ["mydevice", "multicolor"]
            
            def __init__(self):
                super().__init__()
                self._detect_sysfs_led_path()
    """
    
    # Subclasses can override this to define device-specific search keywords
    # 子类可以覆盖此属性来定义设备特定的搜索关键词
    SYSFS_LED_PATHS: list[str] = []
    
    def __init__(self):
        super().__init__()
        self._sysfs_led_path: Optional[str] = None
    
    def _detect_sysfs_led_path(self) -> Optional[str]:
        """
        Detect and store the sysfs LED path for this device.
        检测并存储该设备的 sysfs LED 路径。
        
        Returns:
            Optional[str]: The detected sysfs path, or None if not found
        """
        # Try the default LED_PATH first
        # 首先尝试默认的 LED_PATH
        if os.path.exists(LED_PATH):
            logger.debug(f"Detected sysfs LED path: {LED_PATH}")
            self._sysfs_led_path = LED_PATH
            return self._sysfs_led_path
        
        # If subclass defines specific paths, search for them
        # 如果子类定义了特定路径，搜索它们
        if self.SYSFS_LED_PATHS:
            led_base_path = "/sys/class/leds/"
            if os.path.exists(led_base_path):
                try:
                    for led_dir in os.listdir(led_base_path):
                        # Check if any of the search keywords match
                        # 检查是否有任何搜索关键词匹配
                        for keyword in self.SYSFS_LED_PATHS:
                            if keyword.lower() in led_dir.lower():
                                full_path = os.path.join(led_base_path, led_dir)
                                # Verify it has the necessary files
                                # 验证它有必需的文件
                                if os.path.exists(os.path.join(full_path, "brightness")) or \
                                   os.path.exists(os.path.join(full_path, "multi_intensity")):
                                    logger.debug(f"Detected sysfs LED path: {full_path}")
                                    self._sysfs_led_path = full_path
                                    return self._sysfs_led_path
                except Exception as e:
                    logger.warning(f"Error searching for sysfs LED paths: {e}")
        
        logger.debug("No sysfs LED path detected")
        self._sysfs_led_path = None
        return None
    
    def _set_color_by_sysfs(self, color: Color, brightness: Optional[int] = None) -> bool:
        """
        Set LED color via sysfs interface.
        通过 sysfs 接口设置 LED 颜色。
        
        This method supports two approaches:
        1. multi_intensity file for RGB control (preferred)
        2. brightness file for single-color/white control (fallback)
        
        该方法支持两种方式：
        1. 用于 RGB 控制的 multi_intensity 文件（首选）
        2. 用于单色/白色控制的 brightness 文件（备用）
        
        Args:
            color (Color): RGB color to set
            brightness (Optional[int]): Brightness level (0-255), if None uses system default
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._sysfs_led_path:
            # Try to detect it if not already done
            # 如果还未检测，尝试检测
            if not self._detect_sysfs_led_path():
                logger.debug("No sysfs LED path available")
                return False
        
        try:
            # Try multi_intensity for RGB control (standard multicolor LED)
            # 尝试使用 multi_intensity 进行 RGB 控制（标准多色 LED）
            multi_intensity_path = os.path.join(self._sysfs_led_path, "multi_intensity")
            if os.path.exists(multi_intensity_path):
                with open(multi_intensity_path, "w") as f:
                    f.write(f"{color.R} {color.G} {color.B}")
                logger.debug(f"Set color via multi_intensity: RGB({color.R}, {color.G}, {color.B})")
            
            # Set brightness if available
            # 如果可用，设置亮度
            brightness_path = os.path.join(self._sysfs_led_path, "brightness")
            if os.path.exists(brightness_path):
                if brightness is None:
                    # Import here to avoid circular dependency
                    # 在此导入以避免循环依赖
                    from config import DEFAULT_BRIGHTNESS
                    brightness = DEFAULT_BRIGHTNESS * 255 // 100
                
                with open(brightness_path, "w") as f:
                    f.write(str(brightness))
                logger.debug(f"Set brightness: {brightness}")
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to set color via sysfs: {e}")
            return False
    
    def _has_sysfs_support(self) -> bool:
        """
        Check if sysfs LED control is available.
        检查 sysfs LED 控制是否可用。
        
        Returns:
            bool: True if sysfs path is detected and valid
        """
        if self._sysfs_led_path is None:
            self._detect_sysfs_led_path()
        return self._sysfs_led_path is not None
    
    # Reserved methods for future multi-zone support
    # 为未来多区域支持保留的方法
    
    def _detect_sysfs_multi_zones(self) -> int:
        """
        Detect number of LED zones available via sysfs.
        检测通过 sysfs 可用的 LED 区域数量。
        
        Returns:
            int: Number of zones detected (1 for single zone/fallback, or actual count for multi-zone)
        """
        if not self._sysfs_led_path:
            return 1
        
        # First try multi_intensity_zones (extended multi-zone support)
        try:
            multi_intensity_zones_path = os.path.join(self._sysfs_led_path, "multi_intensity_zones")
            if os.path.exists(multi_intensity_zones_path):
                with open(multi_intensity_zones_path, "r") as f:
                    values = f.read().strip().split()
                    if values:  # Make sure we got something
                        num_zones = len(values) // 3
                        if num_zones > 0:
                            logger.info(f"Detected {num_zones} LED zones via multi_intensity_zones")
                            return num_zones
        except Exception as e:
            logger.debug(f"Failed to detect multi_intensity_zones: {e}")
        
        # Fallback: check standard multi_intensity (single zone)
        try:
            multi_intensity_path = os.path.join(self._sysfs_led_path, "multi_intensity")
            if os.path.exists(multi_intensity_path):
                logger.debug("Standard multi_intensity detected (single zone)")
                return 1
        except Exception as e:
            logger.debug(f"Failed to detect multi_intensity: {e}")
        
        logger.debug("No sysfs LED zone detection available")
        return 1
    
    def _has_sysfs_multi_zone_support(self) -> bool:
        """
        Check if sysfs multi-zone LED control is available.
        检查 sysfs 多区域 LED 控制是否可用。
        
        Returns:
            bool: True if multi_intensity_zones attribute exists and is writable
        """
        if not self._sysfs_led_path:
            return False
        
        try:
            multi_intensity_zones_path = os.path.join(self._sysfs_led_path, "multi_intensity_zones")
            if not os.path.exists(multi_intensity_zones_path):
                logger.debug("multi_intensity_zones not found")
                return False
            
            # Check if writable (some sysfs files may be read-only)
            if not os.access(multi_intensity_zones_path, os.W_OK):
                logger.debug("multi_intensity_zones exists but is not writable")
                return False
            
            logger.debug("multi_intensity_zones is available")
            return True
            
        except Exception as e:
            logger.debug(f"Error checking multi_intensity_zones: {e}")
            return False
    
    def _set_zones_color_by_sysfs(self, zone_colors: list[tuple[int, int, int]]) -> bool:
        """
        Set colors for multiple LED zones via sysfs multi_intensity_zones.
        通过 sysfs multi_intensity_zones 为多个 LED 区域设置颜色。
        
        This is a generic method that works with any device supporting multi_intensity_zones.
        这是一个通用方法，适用于任何支持 multi_intensity_zones 的设备。
        
        Note: Only works if multi_intensity_zones attribute exists.
        注意：仅在 multi_intensity_zones 属性存在时有效。
        
        Args:
            zone_colors: List of RGB tuples, one per zone [(R,G,B), (R,G,B), ...]
                         RGB 元组列表，每个区域一个 [(R,G,B), (R,G,B), ...]
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._sysfs_led_path:
            logger.debug("No sysfs LED path available")
            return False
        
        # Verify multi_intensity_zones exists before attempting write
        if not self._has_sysfs_multi_zone_support():
            logger.debug("multi_intensity_zones not available, cannot set zone colors")
            return False
        
        try:
            multi_intensity_zones_path = os.path.join(self._sysfs_led_path, "multi_intensity_zones")
            
            # Build the color string: "R G B R G B ..." for all zones
            color_values = []
            for r, g, b in zone_colors:
                # Clamp values to 0-255
                r = max(0, min(255, int(r)))
                g = max(0, min(255, int(g)))
                b = max(0, min(255, int(b)))
                color_values.extend([str(r), str(g), str(b)])
            
            color_string = " ".join(color_values)
            
            with open(multi_intensity_zones_path, "w") as f:
                f.write(color_string)
            
            logger.debug(f"Successfully set {len(zone_colors)} zone colors via multi_intensity_zones")
            return True
            
        except OSError as e:
            logger.warning(f"Failed to write to multi_intensity_zones (OSError): {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to set zone colors via sysfs: {e}")
            return False
    
    def _set_zone_color_by_sysfs(self, zone_idx: int, color: Color) -> bool:
        """
        Set color for a specific LED zone via sysfs.
        通过 sysfs 为特定 LED 区域设置颜色。
        
        Reserved for future implementation when kernel drivers support per-zone control.
        为未来内核驱动支持按区域控制时的实现保留。
        
        Args:
            zone_idx (int): Zone index
            color (Color): RGB color to set
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Reserved for future implementation
        # 为未来实现保留
        logger.debug(f"Per-zone sysfs control not yet implemented (zone {zone_idx})")
        return False

