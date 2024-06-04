import asyncio
import os
import decky_plugin

try:
    from config import logger, IS_LED_SUSPEND_MODE_SUPPORTED
    from huesync import LedControl
    from utils import Color
    from sysInfo import sysInfoManager
    import update

    logger.info("HueSync main.py")
except Exception as e:
    logger.error(e, exc_info=True)


class Plugin:
    async def _main(self):
        self.ledControl = LedControl()
        while True:
            await asyncio.sleep(3)

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
            logger.info(f"set_ledoff")
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

    async def get_language(self):
        try:
            return sysInfoManager.get_language()
        except Exception as e:
            logger.error(e, exc_info=True)
            return ""

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

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        decky_plugin.logger.info("Goodbye World!")
        pass

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky_plugin.logger.info("Migrating")
        # Here's a migration example for logs:
        # - `~/.config/decky-template/template.log` will be migrated to `decky_plugin.DECKY_PLUGIN_LOG_DIR/template.log`
        decky_plugin.migrate_logs(
            os.path.join(
                decky_plugin.DECKY_USER_HOME,
                ".config",
                "decky-template",
                "template.log",
            )
        )
        # Here's a migration example for settings:
        # - `~/homebrew/settings/template.json` is migrated to `decky_plugin.DECKY_PLUGIN_SETTINGS_DIR/template.json`
        # - `~/.config/decky-template/` all files and directories under this root are migrated to `decky_plugin.DECKY_PLUGIN_SETTINGS_DIR/`
        decky_plugin.migrate_settings(
            os.path.join(decky_plugin.DECKY_HOME, "settings", "template.json"),
            os.path.join(decky_plugin.DECKY_USER_HOME, ".config", "decky-template"),
        )
        # Here's a migration example for runtime data:
        # - `~/homebrew/template/` all files and directories under this root are migrated to `decky_plugin.DECKY_PLUGIN_RUNTIME_DIR/`
        # - `~/.local/share/decky-template/` all files and directories under this root are migrated to `decky_plugin.DECKY_PLUGIN_RUNTIME_DIR/`
        decky_plugin.migrate_runtime(
            os.path.join(decky_plugin.DECKY_HOME, "template"),
            os.path.join(
                decky_plugin.DECKY_USER_HOME, ".local", "share", "decky-template"
            ),
        )
