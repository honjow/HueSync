import threading
import os
from config import logging
from helpers import get_user

class SysInfoManager (threading.Thread):
    def __init__(self):
        self._language = "english"
        threading.Thread.__init__(self)
    
    def get_language(self):
        try:
            lang_path=f"/home/{get_user()}/.steam/registry.vdf"
            if os.path.exists(lang_path):
                with open(lang_path, "r") as f:
                    for line in f.readlines():
                        if "language" in line:
                            self._language = line.split('"')[3]
                            break
            else:
                logging.error(f"{lang_path} not found, using default language english")
            logging.info(f"get_language {self._language} path={lang_path}")
            return self._language
        except Exception as e:
            logging.error(e)
            return self._language

sysInfoManager = SysInfoManager()
sysInfoManager.start()