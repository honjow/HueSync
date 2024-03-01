import logging
import os

# 日志配置
try:
    LOG_LOCATION = "/tmp/huesync_py.log"
    logging.basicConfig(
        level=logging.DEBUG,
        filename=LOG_LOCATION,
        format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s",
        filemode="w",
        force=True,
    )
except Exception as e:
    logging.error(f"日志配置异常|{e}")

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

def is_led_supported():
    return os.path.exists(LED_PATH)

IS_LED_SUPPORTED = is_led_supported()

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
