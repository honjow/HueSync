"""
Custom RGB Manager
自定义 RGB 管理器

Centralized management for custom RGB effects across all device types.
集中管理所有设备类型的自定义 RGB 效果。
"""

from config import logger
from custom_zone_animator import KeyframeAnimator


class CustomRgbManager:
    """
    Manager for custom RGB effects (MSI, AyaNeo, ROG Ally).
    自定义 RGB 效果管理器（MSI、AyaNeo、ROG Ally）。
    
    Responsibilities:
    - Validation of custom RGB configurations
    - Device-specific RGB application
    - Animation lifecycle management
    - Mutex handling between different LED effects
    """
    
    # Device zone configuration
    # 设备区域配置
    DEVICE_ZONES = {
        "msi": 9,
        "ayaneo": 8,
        "rog_ally": 4
    }
    
    def __init__(self, led_control):
        """
        Initialize CustomRgbManager.
        初始化 CustomRgbManager。
        
        Args:
            led_control: LedControl instance
        """
        self.led_control = led_control
        self._ayaneo_animator: KeyframeAnimator | None = None
    
    # ===== Validation Methods =====
    # 验证方法
    
    def validate_config(self, device_type: str, config: dict) -> bool:
        """
        Validate custom RGB configuration for any device type.
        统一验证所有设备类型的自定义 RGB 配置。
        
        Args:
            device_type: "msi", "ayaneo", or "rog_ally"
            config: Configuration dict
        
        Returns:
            bool: True if valid
        """
        if device_type not in self.DEVICE_ZONES:
            logger.error(f"Unknown device type: {device_type}")
            return False
        
        expected_zones = self.DEVICE_ZONES[device_type]
        return self._validate_config_internal(config, expected_zones, device_type)
    
    def _validate_config_internal(
        self, 
        config: dict, 
        expected_zones: int, 
        device_name: str = ""
    ) -> bool:
        """
        Internal validation logic (unified for all devices).
        内部验证逻辑（所有设备统一）。
        
        Args:
            config: Configuration dict to validate
            expected_zones: Number of LED zones for this device
            device_name: Device name for error messages
        
        Returns:
            bool: True if valid
        """
        try:
            # Check required fields
            if "speed" not in config or "brightness" not in config or "keyframes" not in config:
                logger.error(f"Missing required fields in {device_name} config")
                return False
            
            # Validate speed (0-20) and brightness (0-100)
            if not isinstance(config["speed"], int) or not 0 <= config["speed"] <= 20:
                logger.error(f"Invalid {device_name} speed: {config['speed']}")
                return False
            
            if not isinstance(config["brightness"], int) or not 0 <= config["brightness"] <= 100:
                logger.error(f"Invalid {device_name} brightness: {config['brightness']}")
                return False
            
            # Validate keyframes (1-8 frames)
            keyframes = config["keyframes"]
            if not isinstance(keyframes, list) or not 1 <= len(keyframes) <= 8:
                logger.error(
                    f"Invalid {device_name} keyframes count: "
                    f"{len(keyframes) if isinstance(keyframes, list) else 'not a list'}"
                )
                return False
            
            # Validate each keyframe
            for frame_idx, frame in enumerate(keyframes):
                if not isinstance(frame, list) or len(frame) != expected_zones:
                    logger.error(
                        f"{device_name} Frame {frame_idx}: must have {expected_zones} zones, "
                        f"got {len(frame) if isinstance(frame, list) else 'not a list'}"
                    )
                    return False
                
                # Validate each zone color
                for zone_idx, zone in enumerate(frame):
                    if not isinstance(zone, list) or len(zone) != 3:
                        logger.error(
                            f"{device_name} Frame {frame_idx}, Zone {zone_idx}: "
                            f"must be [R,G,B], got {zone}"
                        )
                        return False
                    
                    if not all(isinstance(c, int) and 0 <= c <= 255 for c in zone):
                        logger.error(
                            f"{device_name} Frame {frame_idx}, Zone {zone_idx}: "
                            f"RGB values must be 0-255, got {zone}"
                        )
                        return False
            
            return True
        
        except Exception as e:
            logger.error(f"{device_name} config validation error: {e}", exc_info=True)
            return False
    
    # ===== Application Methods =====
    # 应用方法
    
    def apply_custom_rgb(self, device_type: str, custom_config: dict) -> bool:
        """
        Apply custom RGB configuration for any device type.
        为任何设备类型应用自定义 RGB 配置。
        
        Args:
            device_type: "msi", "ayaneo", or "rog_ally"
            custom_config: Configuration dict
        
        Returns:
            bool: True if successful
        """
        if not self.validate_config(device_type, custom_config):
            logger.error(f"Invalid {device_type} custom config")
            return False
        
        # Dispatch to device-specific implementation
        if device_type == "msi":
            return self._apply_msi_custom_rgb(custom_config)
        elif device_type == "ayaneo":
            return self._apply_software_animation(
                custom_config, 
                num_zones=8, 
                device_name="AyaNeo"
            )
        elif device_type == "rog_ally":
            return self._apply_ally_custom_rgb(custom_config)
        else:
            logger.error(f"Unknown device type: {device_type}")
            return False
    
    def _apply_msi_custom_rgb(self, custom_config: dict) -> bool:
        """
        Apply MSI custom RGB (hardware keyframe engine).
        应用 MSI 自定义 RGB（硬件关键帧引擎）。
        """
        try:
            self.stop_all_effects()
            
            device = self.led_control.device
            if not hasattr(device, 'set_custom_preset'):
                logger.error("Device does not support MSI custom RGB")
                return False
            
            success = device.set_custom_preset(
                keyframes=custom_config["keyframes"],
                speed=custom_config["speed"],
                brightness=custom_config["brightness"]
            )
            
            if success:
                logger.info(
                    f"Applied MSI custom RGB: {len(custom_config['keyframes'])} frames, "
                    f"speed={custom_config['speed']}, brightness={custom_config['brightness']}"
                )
            else:
                logger.error("Failed to apply MSI custom RGB")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to apply MSI custom RGB: {e}", exc_info=True)
            return False
    
    def _apply_software_animation(
        self, 
        custom_config: dict, 
        num_zones: int, 
        device_name: str
    ) -> bool:
        """
        Apply software-based keyframe animation (unified for AyaNeo).
        应用基于软件的关键帧动画（AyaNeo 统一）。
        
        Args:
            custom_config: Configuration dict
            num_zones: Number of LED zones
            device_name: Device name for logging
        
        Returns:
            bool: True if successful
        """
        try:
            self.stop_all_effects()
            
            device = self.led_control.device
            if not hasattr(device, 'set_custom_zone_colors'):
                logger.error(f"Device does not support custom zone colors")
                return False
            
            # Convert keyframes to list format
            # 将关键帧转换为列表格式
            converted_keyframes = [
                [[int(c) for c in rgb] for rgb in frame]
                for frame in custom_config["keyframes"]
            ]
            
            # Create callback function for setting zone colors
            # 创建用于设置区域颜色的回调函数
            def set_zones_callback(left_colors: list[list[int]], right_colors: list[list[int]]) -> None:
                """Set LED colors for all zones"""
                # Combine left and right colors into a single list
                # 将左右区域颜色合并为单个列表
                all_colors = left_colors + right_colors
                # Convert to tuple format for device
                # 转换为设备需要的元组格式
                all_colors_tuples = [tuple(rgb) for rgb in all_colors]
                # Call set_custom_zone_colors with the combined colors
                # 使用合并后的颜色调用 set_custom_zone_colors
                device.set_custom_zone_colors(all_colors_tuples)
            
            # Split zones evenly between left and right
            # 将区域平均分配给左右两侧
            num_left = num_zones // 2
            num_right = num_zones - num_left
            
            # Create and start animator
            self._ayaneo_animator = KeyframeAnimator(
                keyframes=converted_keyframes,
                set_zones_callback=set_zones_callback,
                speed=custom_config["speed"],
                brightness=custom_config["brightness"],
                num_left_zones=num_left,
                num_right_zones=num_right
            )
            self._ayaneo_animator.start()
            
            logger.info(
                f"Started {device_name} custom RGB animation: "
                f"{len(custom_config['keyframes'])} frames, "
                f"speed={custom_config['speed']}, brightness={custom_config['brightness']}"
            )
            return True
        
        except Exception as e:
            logger.error(f"Failed to apply {device_name} custom RGB: {e}", exc_info=True)
            return False
    
    def _apply_ally_custom_rgb(self, custom_config: dict) -> bool:
        """
        Apply ROG Ally custom RGB (device-managed software animation).
        应用 ROG Ally 自定义 RGB（设备管理的软件动画）。
        """
        try:
            self.stop_all_effects()
            
            device = self.led_control.device
            if not hasattr(device, 'start_custom_animation'):
                logger.error("Device does not support custom animation")
                return False
            
            # Convert keyframes
            keyframes = [
                [tuple(zone) for zone in frame]
                for frame in custom_config["keyframes"]
            ]
            
            # Ally device manages its own animation
            success = device.start_custom_animation(
                keyframes=keyframes,
                speed=custom_config["speed"],
                brightness=custom_config["brightness"]
            )
            
            if success:
                logger.info(
                    f"Started Ally custom RGB animation: "
                    f"{len(custom_config['keyframes'])} frames, "
                    f"speed={custom_config['speed']}, brightness={custom_config['brightness']}"
                )
            else:
                logger.error("Failed to start Ally custom animation")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to apply Ally custom RGB: {e}", exc_info=True)
            return False
    
    # ===== Lifecycle Management =====
    # 生命周期管理
    
    def stop_all_effects(self):
        """
        Stop all LED effects (software effects and custom RGB animators).
        停止所有 LED 效果（软件效果和自定义 RGB 动画器）。
        """
        stopped_any = False
        
        # Stop AyaNeo software animator
        if self._ayaneo_animator and self._ayaneo_animator.is_running():
            self._ayaneo_animator.stop()
            logger.info("Stopped AyaNeo custom RGB animator")
            stopped_any = True
        
        # Stop Ally custom animation
        try:
            device = self.led_control.device
            if hasattr(device, 'is_custom_animation_running') and device.is_custom_animation_running():
                device.stop_custom_animation()
                logger.info("Stopped Ally custom RGB animation")
                stopped_any = True
        except Exception as e:
            logger.debug(f"Error stopping Ally custom animation: {e}")
        
        # Stop device software effects (Pulse, Rainbow, etc.)
        try:
            device = self.led_control.device
            if hasattr(device, 'stop_effects'):
                device.stop_effects()
                if stopped_any:
                    logger.debug("Stopped software LED effects")
                stopped_any = True
        except Exception as e:
            logger.debug(f"Error stopping software effects: {e}")
        
        return stopped_any

