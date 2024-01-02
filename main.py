import subprocess
import asyncio
import os
import sys

#获取插件路径 加载backend中各个py文件
try:
    from helpers import get_homebrew_path
    HOMEBREW_PATH = get_homebrew_path()   
    sys.path.append("{}/plugins/ayaled/backend".format(HOMEBREW_PATH))
    from config import logging
    from ayaled import AyaLed,Color
    logging.info("ayaled main.py")
except Exception as e:
    logging.error(e)

class Plugin:
    async def _main(self):
        while True:
            await asyncio.sleep(3)

    def set_ledOn(self, r: int, g: int, b: int):
        try:
            AyaLed.set_all_pixels(Color(r,g,b))
            logging.info(f"set_ledOn:{r},{g},{b}")
        except Exception as e:
            logging.error(e)
            return False
    
    def set_ledOff(self):
        try:
            AyaLed.set_all_pixels(Color(0,0,0))
            logging.info(f"set_ledoff")
        except Exception as e:
            logging.error(e)
            return False
