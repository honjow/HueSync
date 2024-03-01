import asyncio
import sys

# 获取插件路径 加载backend中各个py文件
try:
    from helpers import get_homebrew_path

    HOMEBREW_PATH = get_homebrew_path()
    sys.path.append("{}/plugins/HueSync/backend".format(HOMEBREW_PATH))
    from config import logging
    from huesync import LedControl, Color
    from sysInfo import sysInfoManager
    import update

    logging.info("HueSync main.py")
except Exception as e:
    logging.error(e)


class Plugin:
    async def _main(self):
        while True:
            await asyncio.sleep(3)

    def setRGB(self, r: int, g: int, b: int, brightness: int = 100):
        try:
            logging.info(f"set_ledOn:{r},{g},{b}, brightness={brightness}")
            LedControl.set_Color(Color(r, g, b), brightness=100)
        except Exception as e:
            logging.error(e)
            return False

    def setOff(self):
        try:
            LedControl.set_Color(Color(0, 0, 0), brightness=0)
            logging.info(f"set_ledoff")
        except Exception as e:
            logging.error(e)
            return False
    
    async def get_language(self):
        try:
            return sysInfoManager.get_language()
        except Exception as e:
            logging.error(e)
            return ""
        
    async def update_latest(self):
        logging.info("Updating latest")
        return update.update_latest()
    
    async def get_version(self):
        return update.get_version()
    
    async def get_latest_version(self):
        return update.get_latest_version()
