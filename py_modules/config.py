import logging
import os
import traceback

from logging_handler import SystemdHandler

# 日志配置
LOG_LOCATION = "/tmp/huesync_py.log"
try:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s",
        force=True,
        handlers=[
            SystemdHandler(),
            logging.FileHandler(filename=LOG_LOCATION, mode="w"),
        ],
    )
except Exception as e:
    stack = traceback.format_exc()
    with open(LOG_LOCATION, "a") as f:
        f.write(str(e))
        f.write(stack)

logger = logging.getLogger(__name__)

# 设备信息获取配置
try:
    PRODUCT_NAME = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
except Exception as e:
    logging.error(f"设备信息配置异常|{e}")

# sys_vendor
try:
    SYS_VENDOR = open("/sys/devices/virtual/dmi/id/sys_vendor", "r").read().strip()
except Exception as e:
    logging.error(f"设备信息配置异常|{e}")

LED_PATH = "/sys/class/leds/multicolor:chassis/"
LED_MODE_PATH = os.path.join(LED_PATH, "device", "led_mode")

# Value: oem, off, keep. Default: oem
LED_SUSPEND_MODE_PATH = os.path.join(LED_PATH, "suspend_mode")

def is_led_supported():
    return os.path.exists(LED_PATH)

def is_led_suspend_mode_supported():
    return os.path.exists(LED_SUSPEND_MODE_PATH)

IS_LED_SUPPORTED = is_led_supported()
IS_LED_SUSPEND_MODE_SUPPORTED = is_led_suspend_mode_supported()


AYANEO_EC_SUPPORT_LIST = [
    "AIR",
    "AIR Pro",
    "AIR 1S",
    "AIR 1S Limited",
    "AYANEO 2",
    "AYANEO 2S",
    "GEEK",
    "GEEK 1S",
]

IS_AYANEO_EC_SUPPORTED = PRODUCT_NAME in AYANEO_EC_SUPPORT_LIST

API_URL = "https://api.github.com/repos/honjow/HueSync/releases/latest"
