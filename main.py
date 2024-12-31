import os

import decky

try:
    import update
    from config import IS_LED_SUSPEND_MODE_SUPPORTED, logger
    from huesync import LedControl
    from utils import Color

    decky.logger.info("HueSync main.py")
except Exception as e:
    decky.logger.error(e, exc_info=True)


class Plugin:
    async def _main(self):
        try:
            self.ledControl = LedControl()
        except Exception as e:
            logger.error(e, exc_info=True)

    async def setRGB(self, r: int, g: int, b: int, brightness: int = 100):
        try:
            logger.info(f"set_ledOn:{r},{g},{b}, brightness={brightness}")
            self.ledControl.set_Color(Color(r, g, b), brightness=100)
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def setOff(self):
        try:
            self.ledControl.set_Color(Color(0, 0, 0), brightness=0)
            logger.info("set_ledoff")
        except Exception as e:
            logger.error(e)
            return False

    async def get_suspend_mode(self):
        try:
            return self.ledControl.get_suspend_mode()
        except Exception as e:
            logger.error(e, exc_info=True)
            return ""

    async def set_suspend_mode(self, mode: str):
        try:
            if IS_LED_SUSPEND_MODE_SUPPORTED:
                self.ledControl.set_suspend_mode(mode)
                return True
            else:
                return False
        except Exception as e:
            logger.error(e, exc_info=True)
            return False

    async def is_support_suspend_mode(self):
        return IS_LED_SUSPEND_MODE_SUPPORTED

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

    async def get_mode_capabilities(self) -> dict[str, dict]:
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
                mode: {
                    "mode": cap.mode.value,
                    "supports_color": cap.supports_color,
                    "supports_color2": cap.supports_color2,
                    "supports_brightness": cap.supports_brightness,
                    "supports_speed": cap.supports_speed,
                }
                for mode, cap in capabilities.items()
            }
        except Exception as e:
            logger.error(e, exc_info=True)
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
