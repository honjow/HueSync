import os

import decky
from settings import SettingsManager

try:
    import update
    from config import CONFIG_KEY, logger
    from huesync import LedControl

    decky.logger.info("HueSync main.py")
except Exception as e:
    decky.logger.error(e, exc_info=True)


class Plugin:
    async def _main(self):
        self.settings = SettingsManager(
            name="config", settings_directory=decky.DECKY_PLUGIN_SETTINGS_DIR
        )
        try:
            self.ledControl = LedControl()
        except Exception as e:
            logger.error(e, exc_info=True)

    async def get_settings(self):
        return self.settings.getSetting(CONFIG_KEY)

    async def set_settings(self, settings):
        self.settings.setSetting(CONFIG_KEY, settings)
        logger.debug(f"save Settings: {settings}")
        return True

    async def set_color(
        self,
        mode: str | None = None,
        r: int | None = None,
        g: int | None = None,
        b: int | None = None,
        r2: int | None = None,
        g2: int | None = None,
        b2: int | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
        brightness_level: str | None = None,
        zone_colors: dict | None = None,
        zone_enabled: dict | None = None,
    ):
        try:
            from utils import Color, RGBMode

            # Custom RGB is handled separately by device-specific implementations
            # 自定义 RGB 由设备特定实现单独处理
            # - MSI: hardware-based keyframes
            # - AyaNeo: software-based animator
            # Skip standard set_color processing for custom mode
            if mode and mode.lower() == "custom":
                # Stop AyaNeo animator if it's running (when switching away from custom)
                # 停止 AyaNeo 动画器（如果正在运行）
                if self._ayaneo_animator and self._ayaneo_animator.is_running():
                    self._ayaneo_animator.stop()
                    logger.info("Stopped AyaNeo animator (switching modes)")
                logger.debug("Skipping set_color for custom mode (use set_custom_rgb)")
                return True

            color = None
            color2 = None
            if r is not None and g is not None and b is not None:
                color = Color(r, g, b)
            if r2 is not None and g2 is not None and b2 is not None:
                color2 = Color(r2, g2, b2)

            # Convert zone_colors dict to Color objects
            # 将 zone_colors 字典转换为 Color 对象
            zone_colors_converted = None
            if zone_colors:
                zone_colors_converted = {}
                for zone_id, color_dict in zone_colors.items():
                    if color_dict and 'R' in color_dict and 'G' in color_dict and 'B' in color_dict:
                        zone_colors_converted[zone_id] = Color(
                            color_dict['R'],
                            color_dict['G'],
                            color_dict['B']
                        )

            rgb_mode = (
                next((m for m in RGBMode if m.value == mode.lower()), None)
                if mode
                else None
            )
            self.ledControl.set_color(
                rgb_mode, color, color2, zone_colors=zone_colors_converted, zone_enabled=zone_enabled, init=init, brightness=brightness, speed=speed, brightness_level=brightness_level
            )
            return True
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def get_suspend_mode(self):
        try:
            return self.ledControl.get_suspend_mode()
        except Exception as e:
            logger.error(e, exc_info=True)
            return ""

    async def set_suspend_mode(self, mode: str):
        try:
            self.ledControl.set_suspend_mode(mode)
            return True
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def is_support_suspend_mode(self):
        return self.ledControl.get_suspend_mode() != ""

    async def suspend(self):
        self.ledControl.suspend()

    async def resume(self):
        self.ledControl.resume()

    async def update_latest(self):
        logger.info("Updating latest")
        try:
            return update.update_latest()
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def get_version(self):
        try:
            return update.get_version()
        except Exception as e:
            logger.error(e, exc_info=True)
            return ""

    async def get_latest_version(self):
        try:
            return update.get_latest_version()
        except Exception as e:
            logger.error(e, exc_info=True)
            return ""

    async def log_info(self, message: str):
        try:
            return logger.info(f"Frontend: {message}")
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def log_error(self, message: str):
        try:
            return logger.error(f"Frontend: {message}")
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def log_warn(self, message: str):
        try:
            return logger.warn(f"Frontend: {message}")
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def log_debug(self, message: str):
        try:
            return logger.debug(f"Frontend: {message}")
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def get_mode_capabilities(self):
        """
        Get the capabilities of each supported RGB mode.
        获取每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[str, dict]: A dictionary mapping mode names to their capabilities.
                Each capability describes what features (color, brightness, etc.) are supported by the mode.
                The capabilities are converted to a dictionary for JSON serialization.
            dict[str, dict]: 模式名称到其功能支持情况的映射字典。
                每个功能支持情况描述该模式支持的特性（颜色、亮度等）。
                功能支持情况会被转换为字典以便进行 JSON 序列化。
        """
        try:
            capabilities = self.ledControl.get_mode_capabilities()
            # Convert RGBModeCapabilities objects to dictionaries for JSON serialization
            return {
                mode.value: {
                    "mode": mode.value,
                    "color": cap.color,
                    "color2": cap.color2,
                    "speed": cap.speed,
                    "brightness": cap.brightness,
                    "brightness_level": cap.brightness_level,
                    "zones": cap.zones,  # Add zones field
                }
                for mode, cap in capabilities.items()
            }
        except Exception as e:
            logger.error(e, exc_info=True)
            return {}

    async def get_device_capabilities(self):
        """
        Get device hardware capabilities.
        获取设备硬件能力。

        Returns:
            dict: Device capabilities including power_led support
        """
        try:
            return self.ledControl.get_device_capabilities()
        except Exception as e:
            logger.error(f"Failed to get device capabilities: {e}", exc_info=True)
            return {"power_led": False}

    async def set_power_light(self, enabled: bool):
        """
        Set power LED state.
        设置电源灯状态。

        Args:
            enabled (bool): True to turn on, False to turn off

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.ledControl.set_power_light(enabled)
            if success:
                logger.info(f"Power LED set to: {'ON' if enabled else 'OFF'}")
            else:
                logger.warning(f"Failed to set power LED to: {'ON' if enabled else 'OFF'}")
            return success
        except Exception as e:
            logger.error(f"Failed to set power light: {e}", exc_info=True)
            return False

    async def get_power_light(self):
        """
        Get power LED state.
        获取电源灯状态。

        Returns:
            bool | None: True if on, False if off, None if not supported or failed
        """
        try:
            status = self.ledControl.get_power_light()
            if status is not None:
                logger.debug(f"Power LED status: {'ON' if status else 'OFF'}")
            return status
        except Exception as e:
            logger.error(f"Failed to get power light: {e}", exc_info=True)
            return None

    # ===== Unified Custom RGB API =====
    # 统一的自定义 RGB API
    # Provides device-agnostic interface for multi-zone custom RGB
    # 为多区域自定义 RGB 提供设备无关的接口

    # Unified custom RGB presets key for all device types
    # 所有设备类型共享的统一自定义 RGB 预设 key
    CUSTOM_RGB_PRESETS_KEY = "custom_rgb_presets"

    async def get_custom_rgb_presets(self, device_type: str):
        """
        Get all custom RGB presets for any device type.
        获取任何设备类型的所有自定义 RGB 预设。
        
        All device types share the same preset storage.
        所有设备类型共享同一个预设存储。
        """
        try:
            presets = self.settings.getSetting(self.CUSTOM_RGB_PRESETS_KEY)
            if presets is None:
                presets = {}
            logger.debug(f"Retrieved {len(presets)} custom RGB presets")
            return presets if isinstance(presets, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get custom RGB presets: {e}", exc_info=True)
            return {}

    async def save_custom_rgb_preset(self, device_type: str, name: str, config: dict):
        """
        Save a custom RGB preset for any device type.
        为任何设备类型保存自定义 RGB 预设。
        """
        try:
            # Validate config
            if device_type == "msi":
                if not self._validate_msi_custom_config(config):
                    logger.error(f"Invalid MSI custom preset config")
                    return False
            elif device_type == "ayaneo":
                if not self._validate_ayaneo_custom_config(config):
                    logger.error(f"Invalid AyaNeo custom preset config")
                    return False
            else:
                logger.error(f"Unknown device type: {device_type}")
                return False

            # Get existing presets
            presets = await self.get_custom_rgb_presets(device_type)
            presets[name] = config
            
            # Save to unified storage
            self.settings.setSetting(self.CUSTOM_RGB_PRESETS_KEY, presets)
            logger.info(f"Saved custom RGB preset '{name}' (device: {device_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to save {device_type} preset '{name}': {e}", exc_info=True)
            return False

    async def delete_custom_rgb_preset(self, device_type: str, name: str):
        """
        Delete a custom RGB preset for any device type.
        删除任何设备类型的自定义 RGB 预设。
        """
        try:
            presets = await self.get_custom_rgb_presets(device_type)
            if name not in presets:
                logger.warning(f"{device_type.upper()} preset '{name}' not found")
                return False

            del presets[name]
            self.settings.setSetting(self.CUSTOM_RGB_PRESETS_KEY, presets)
            logger.info(f"Deleted custom RGB preset '{name}' (device: {device_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {device_type} preset '{name}': {e}", exc_info=True)
            return False

    async def apply_custom_rgb_preset(self, device_type: str, name: str):
        """
        Apply a custom RGB preset for any device type.
        应用任何设备类型的自定义 RGB 预设。
        """
        try:
            presets = await self.get_custom_rgb_presets(device_type)
            if name not in presets:
                logger.error(f"{device_type.upper()} preset '{name}' not found")
                return False

            config = presets[name]
            return await self.set_custom_rgb(device_type, config)
        except Exception as e:
            logger.error(f"Failed to apply {device_type} preset '{name}': {e}", exc_info=True)
            return False

    async def set_custom_rgb(self, device_type: str, custom_config: dict):
        """
        Apply custom RGB configuration for any device type.
        为任何设备类型应用自定义 RGB 配置。
        
        Unified interface - device-specific implementation is dispatched internally.
        统一接口 - 设备特定实现在内部分发。
        
        Args:
            device_type: "msi" or "ayaneo"
            custom_config: Configuration dict with speed, brightness, and keyframes
            
        Returns:
            bool: True if successful
        """
        if device_type == "msi":
            return await self._apply_msi_custom_rgb(custom_config)
        elif device_type == "ayaneo":
            return await self._apply_ayaneo_custom_rgb(custom_config)
        else:
            logger.error(f"Unknown device type: {device_type}")
            return False

    # ===== MSI Custom RGB Methods (Device-Specific Implementation) =====
    # MSI 自定义 RGB 方法（设备特定实现）

    def _validate_msi_custom_config(self, config: dict) -> bool:
        """
        Validate MSI custom RGB configuration.
        验证 MSI 自定义 RGB 配置。

        Args:
            config: Configuration dict to validate

        Returns:
            bool: True if valid
        """
        try:
            # Check required fields
            if "speed" not in config or "brightness" not in config or "keyframes" not in config:
                logger.error("Missing required fields in config")
                return False

            # Validate speed (0-20)
            if not isinstance(config["speed"], int) or not 0 <= config["speed"] <= 20:
                logger.error(f"Invalid speed: {config['speed']}")
                return False

            # Validate brightness (0-100)
            if not isinstance(config["brightness"], int) or not 0 <= config["brightness"] <= 100:
                logger.error(f"Invalid brightness: {config['brightness']}")
                return False

            # Validate keyframes (1-8 frames)
            keyframes = config["keyframes"]
            if not isinstance(keyframes, list) or not 1 <= len(keyframes) <= 8:
                logger.error(f"Invalid keyframes count: {len(keyframes) if isinstance(keyframes, list) else 'not a list'}")
                return False

            # Validate each keyframe
            for frame_idx, frame in enumerate(keyframes):
                # Must have exactly 9 zones
                if not isinstance(frame, list) or len(frame) != 9:
                    logger.error(f"Frame {frame_idx}: must have 9 zones, got {len(frame) if isinstance(frame, list) else 'not a list'}")
                    return False

                # Validate each zone color
                for zone_idx, zone in enumerate(frame):
                    if not isinstance(zone, list) or len(zone) != 3:
                        logger.error(f"Frame {frame_idx}, Zone {zone_idx}: must be [R,G,B], got {zone}")
                        return False
                    # Check RGB values (0-255)
                    if not all(isinstance(c, int) and 0 <= c <= 255 for c in zone):
                        logger.error(f"Frame {frame_idx}, Zone {zone_idx}: RGB values must be 0-255, got {zone}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return False

    async def _apply_msi_custom_rgb(self, custom_config: dict):
        """
        Apply MSI custom RGB configuration (device-specific implementation).
        应用 MSI 自定义 RGB 配置（设备特定实现）。

        Args:
            custom_config: Configuration dict with speed, brightness, and keyframes

        Returns:
            bool: True if successful
        """
        try:
            from utils import Color
            from led.msi_led_device_hid import MSIRGBConfig, MSIKeyFrame, MSIEffect, normalize_speed

            # Validate config
            if not self._validate_msi_custom_config(custom_config):
                logger.error(f"Invalid MSI custom config: {custom_config}")
                return False

            # Build keyframes
            keyframes = []
            for frame_data in custom_config["keyframes"]:
                colors = [
                    Color(zone[0], zone[1], zone[2])
                    for zone in frame_data
                ]
                keyframes.append(MSIKeyFrame(rgb_zones=colors))

            # Build MSI config
            msi_config = MSIRGBConfig(
                speed=normalize_speed(custom_config["speed"]),
                brightness=custom_config["brightness"],
                effect=MSIEffect.UNKNOWN_09,
                keyframes=keyframes
            )

            # Get MSI LED device from ledControl
            if not hasattr(self.ledControl.device, 'led_device'):
                logger.error("Device does not support MSI custom RGB")
                return False

            # Send to device
            success = self.ledControl.device.led_device.send_rgb_config(msi_config)

            if success:
                logger.info(f"Applied MSI custom RGB config with {len(keyframes)} keyframes")
            else:
                logger.error("Failed to send MSI custom RGB config to device")

            return success

        except Exception as e:
            logger.error(f"Failed to apply MSI custom RGB: {e}", exc_info=True)
            return False

    # ===== AyaNeo Custom RGB Methods (Device-Specific Implementation) =====
    # AyaNeo 自定义 RGB 方法（设备特定实现）

    _ayaneo_animator = None  # KeyframeAnimator instance

    def _validate_ayaneo_custom_config(self, config: dict) -> bool:
        """
        Validate AyaNeo custom RGB configuration.
        验证 AyaNeo 自定义 RGB 配置。

        Args:
            config: Configuration dict to validate

        Returns:
            bool: True if valid
        """
        try:
            # Check required fields
            if "speed" not in config or "brightness" not in config or "keyframes" not in config:
                logger.error("Missing required fields in AyaNeo config")
                return False

            # Validate speed (0-20) and brightness (0-100)
            if not isinstance(config["speed"], int) or not 0 <= config["speed"] <= 20:
                logger.error(f"Invalid speed: {config['speed']}")
                return False
            if not isinstance(config["brightness"], int) or not 0 <= config["brightness"] <= 100:
                logger.error(f"Invalid brightness: {config['brightness']}")
                return False

            # Validate keyframes (1-8 frames)
            keyframes = config["keyframes"]
            if not isinstance(keyframes, list) or not 1 <= len(keyframes) <= 8:
                logger.error(f"Invalid keyframes count: {len(keyframes) if isinstance(keyframes, list) else 'not a list'}")
                return False

            # Determine expected zones based on device
            # Note: Need to check device model to determine if it's KUN (9 zones) or standard (8 zones)
            expected_zones = 8  # Default to 8 zones
            if hasattr(self.ledControl.device, 'model'):
                from led.ayaneo_led_device_ec import AyaNeoModel
                if self.ledControl.device.model == AyaNeoModel.KUN:
                    expected_zones = 9

            # Validate each keyframe
            for frame_idx, frame in enumerate(keyframes):
                if not isinstance(frame, list) or len(frame) != expected_zones:
                    logger.error(f"Frame {frame_idx}: must have {expected_zones} zones, got {len(frame) if isinstance(frame, list) else 'not a list'}")
                    return False
                # Validate each zone color
                for zone_idx, zone in enumerate(frame):
                    if not isinstance(zone, list) or len(zone) != 3:
                        logger.error(f"Frame {frame_idx}, Zone {zone_idx}: must be [R,G,B], got {zone}")
                        return False
                    # Check RGB values (0-255)
                    if not all(isinstance(c, int) and 0 <= c <= 255 for c in zone):
                        logger.error(f"Frame {frame_idx}, Zone {zone_idx}: RGB values must be 0-255, got {zone}")
                        return False

            return True

        except Exception as e:
            logger.error(f"AyaNeo config validation error: {e}", exc_info=True)
            return False

    async def _apply_ayaneo_custom_rgb(self, custom_config: dict):
        """
        Apply AyaNeo custom RGB configuration with KeyframeAnimator (device-specific implementation).
        使用 KeyframeAnimator 应用 AyaNeo 自定义 RGB 配置（设备特定实现）。

        Args:
            custom_config: Configuration dict with speed, brightness, and keyframes

        Returns:
            bool: True if successful
        """
        try:
            # Validate config
            if not self._validate_ayaneo_custom_config(custom_config):
                logger.error("Invalid AyaNeo custom RGB configuration")
                return False

            # Stop existing animator if running
            if self._ayaneo_animator and self._ayaneo_animator.is_running():
                self._ayaneo_animator.stop()
                logger.info("Stopped existing AyaNeo animator")

            # Import animator
            from custom_zone_animator import KeyframeAnimator

            # Get device reference
            device = self.ledControl.device
            if not hasattr(device, 'set_custom_zone_colors'):
                logger.error("Device does not support custom zone colors")
                return False

            # Create animator
            self._ayaneo_animator = KeyframeAnimator(
                keyframes=custom_config["keyframes"],
                set_zones_callback=device.set_custom_zone_colors,
                speed=custom_config["speed"],
                brightness=custom_config["brightness"],
                update_rate=30.0,  # 30 FPS
                num_left_zones=4,
                num_right_zones=4
            )

            # Start animation
            self._ayaneo_animator.start()

            logger.info(
                f"Started AyaNeo custom RGB animation: "
                f"{len(custom_config['keyframes'])} frames, "
                f"speed={custom_config['speed']}, "
                f"brightness={custom_config['brightness']}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to apply AyaNeo custom RGB: {e}", exc_info=True)
            return False

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        decky.logger.info("Goodbye World!")
        pass

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("Migrating")
        # Here's a migration example for logs:
        # - `~/.config/decky-template/template.log` will be migrated to `decky.DECKY_PLUGIN_LOG_DIR/template.log`
        decky.migrate_logs(
            os.path.join(
                decky.DECKY_USER_HOME,
                ".config",
                "decky-template",
                "template.log",
            )
        )
        # Here's a migration example for settings:
        # - `~/homebrew/settings/template.json` is migrated to `decky.DECKY_PLUGIN_SETTINGS_DIR/template.json`
        # - `~/.config/decky-template/` all files and directories under this root are migrated to `decky.DECKY_PLUGIN_SETTINGS_DIR/`
        decky.migrate_settings(
            os.path.join(decky.DECKY_HOME, "settings", "template.json"),
            os.path.join(decky.DECKY_USER_HOME, ".config", "decky-template"),
        )
        # Here's a migration example for runtime data:
        # - `~/homebrew/template/` all files and directories under this root are migrated to `decky.DECKY_PLUGIN_RUNTIME_DIR/`
        # - `~/.local/share/decky-template/` all files and directories under this root are migrated to `decky.DECKY_PLUGIN_RUNTIME_DIR/`
        decky.migrate_runtime(
            os.path.join(decky.DECKY_HOME, "template"),
            os.path.join(decky.DECKY_USER_HOME, ".local", "share", "decky-template"),
        )
