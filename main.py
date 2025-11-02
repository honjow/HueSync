import os

import decky
from settings import SettingsManager

try:
    import update
    from config import CONFIG_KEY, logger
    from custom_rgb_manager import CustomRgbManager
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
            self.custom_rgb_manager = CustomRgbManager(self.ledControl)
        except Exception as e:
            logger.error(e, exc_info=True)

    async def get_settings(self):
        return self.settings.getSetting(CONFIG_KEY)

    async def set_settings(self, settings):
        self.settings.setSetting(CONFIG_KEY, settings)
        logger.debug(f"save Settings: {settings}")
        return True

    def _stop_all_led_effects(self):
        """
        Stop all LED effects (software effects and custom RGB animator).
        停止所有 LED 效果（软件效果和自定义 RGB 动画器）。
        
        Delegates to CustomRgbManager for centralized management.
        委托给 CustomRgbManager 进行集中管理。
        """
        return self.custom_rgb_manager.stop_all_effects()

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

            # Custom RGB is handled separately - don't interfere with it
            # 自定义 RGB 单独处理 - 不要干扰它
            # Check this BEFORE stopping effects to avoid stopping active custom animations
            # 在停止效果之前检查，避免停止活动的自定义动画
            if mode and mode.lower() == "custom":
                logger.debug("Skipping set_color for custom mode (already active)")
                return True

            # Stop all LED effects before switching to standard modes
            # 切换到标准模式前停止所有 LED 效果
            self._stop_all_led_effects()

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
            mode = self.ledControl.get_suspend_mode()
            logger.debug(f"get_suspend_mode() -> '{mode}'")
            return mode
        except Exception as e:
            logger.error(f"get_suspend_mode() failed: {e}", exc_info=True)
            return ""

    async def set_suspend_mode(self, mode: str):
        try:
            logger.debug(f"set_suspend_mode('{mode}') called from frontend")
            self.ledControl.set_suspend_mode(mode)
            return True
        except Exception as e:
            logger.error(f"set_suspend_mode('{mode}') failed: {e}", exc_info=True)
            return False

    async def is_support_suspend_mode(self):
        return self.ledControl.get_suspend_mode() != ""

    async def suspend(self):
        """
        Handle system suspend event.
        处理系统睡眠事件。
        
        Reads user settings and passes them to device for suspend handling.
        读取用户设置并传递给设备进行睡眠处理。
        """
        try:
            # Read user settings
            # 读取用户设置
            settings_data = await self.get_settings()
            suspend_settings = {
                'power_led_suspend_off': settings_data.get('powerLedSuspendOff', False)
            }
            
            # Pass settings to device
            # 将设置传递给设备
            self.ledControl.suspend(suspend_settings)
        except Exception as e:
            logger.error(f"Failed to handle suspend: {e}", exc_info=True)

    async def resume(self):
        """
        Handle system resume event.
        处理系统唤醒事件。
        
        Reads user settings and passes them to device for resume handling.
        读取用户设置并传递给设备进行唤醒处理。
        """
        try:
            # Read user settings
            # 读取用户设置
            settings_data = await self.get_settings()
            resume_settings = {
                'power_led_suspend_off': settings_data.get('powerLedSuspendOff', False)
            }
            
            # Pass settings to device
            # 将设置传递给设备
            self.ledControl.resume(resume_settings)
        except Exception as e:
            logger.error(f"Failed to handle resume: {e}", exc_info=True)

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
            # Validate config using unified method from custom_rgb_manager
            # 使用 custom_rgb_manager 的统一验证方法
            if not self.custom_rgb_manager.validate_config(device_type, config):
                logger.error(f"Invalid {device_type} custom preset config")
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
                logger.error(f"{device_type.upper()} preset '{name}' not found in {list(presets.keys())}")
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
        
        Args:
            device_type: "msi", "ayaneo", or "rog_ally"
            custom_config: Configuration dict with speed, brightness, and keyframes
            
        Returns:
            bool: True if successful
        """
        return self.custom_rgb_manager.apply_custom_rgb(device_type, custom_config)

    async def get_led_capabilities(self) -> dict:
        """
        Get LED control capabilities for current device
        获取当前设备的 LED 控制能力
        
        DEPRECATED: Use get_device_capabilities() instead, which includes led_capabilities.
        已废弃：请使用 get_device_capabilities()，它包含 led_capabilities。
        
        Returns:
            dict: LED capabilities including sysfs/EC support and legacy EC detection
        """
        try:
            if hasattr(self.ledControl, 'device') and hasattr(self.ledControl.device, 'get_led_capabilities'):
                return self.ledControl.device.get_led_capabilities()
            return {}
        except Exception as e:
            logger.error(f"Error getting LED capabilities: {e}")
            return {}

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
