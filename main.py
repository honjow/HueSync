import os

import decky
from settings import SettingsManager

try:
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
    ):
        try:
            from utils import Color, RGBMode

            color = None
            color2 = None
            if r is not None and g is not None and b is not None:
                color = Color(r, g, b)
            if r2 is not None and g2 is not None and b2 is not None:
                color2 = Color(r2, g2, b2)

            rgb_mode = (
                next((m for m in RGBMode if m.value == mode.lower()), None)
                if mode
                else None
            )
            self.ledControl.set_color(
                rgb_mode, color, color2, init=init, brightness=brightness, speed=speed, brightness_level=brightness_level
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

    # async def update_latest(self):
    #     logger.info("Updating latest")
    #     try:
    #         return update.update_latest()
    #     except Exception as e:
    #         logger.error(e, exc_info=True)
    #         return False

    # async def get_version(self):
    #     try:
    #         return update.get_version()
    #     except Exception as e:
    #         logger.error(e, exc_info=True)
    #         return ""

    # async def get_latest_version(self):
    #     try:
    #         return update.get_latest_version()
    #     except Exception as e:
    #         logger.error(e, exc_info=True)
    #         return ""

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
