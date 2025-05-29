import logging
import os

import decky
from logging_handler import SystemdHandler

CONFIG_KEY = "huesync_config"

# 日志配置
LOG_LOCATION = "/tmp/huesync_py.log"
LOG_LEVEL = logging.DEBUG


def setup_logger():
    # 定义日志格式
    file_format = "[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s"
    systemd_format = "[%(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s"

    # 创建并配置 handlers
    systemd_handler = SystemdHandler()
    systemd_handler.setFormatter(logging.Formatter(systemd_format))

    file_handler = logging.FileHandler(filename=LOG_LOCATION, mode="w")
    file_handler.setFormatter(logging.Formatter(file_format))

    # 获取 logger
    try:
        logger = decky.logger
    except Exception:
        logger = logging.getLogger(__name__)

    logger.setLevel(LOG_LEVEL)
    logger.addHandler(systemd_handler)
    logger.addHandler(file_handler)

    return logger


# 初始化 logger
logger = setup_logger()

# 设备信息获取配置
try:
    PRODUCT_NAME = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
except Exception as e:
    logger.error(f"设备信息配置异常{e}", exc_info=True)

# sys_vendor
try:
    SYS_VENDOR = open("/sys/devices/virtual/dmi/id/sys_vendor", "r").read().strip()
except Exception as e:
    logger.error(f"设备信息配置异常{e}", exc_info=True)

LED_PATH_LIST = [
    "/sys/class/leds/ayaneo:rgb:joystick_rings",
    "/sys/class/leds/ayn:rgb:joystick_rings",
    "/sys/class/leds/multicolor:chassis",
]

LED_PATH = "/sys/class/leds/multicolor:chassis"
for led_path in LED_PATH_LIST:
    if os.path.exists(led_path):
        LED_PATH = led_path
        break
LED_MODE_PATH = os.path.join(LED_PATH, "device", "led_mode")

# Value: oem, off, keep. Default: oem
LED_SUSPEND_MODE_PATH = os.path.join(LED_PATH, "suspend_mode")

ALLY_LED_PATH = "/sys/class/leds/ally:rgb:joystick_rings"


def is_led_supported():
    return os.path.exists(LED_PATH)


def is_led_suspend_mode_supported():
    return os.path.exists(LED_SUSPEND_MODE_PATH)


IS_LED_SUPPORTED = is_led_supported()
IS_LED_SUSPEND_MODE_SUPPORTED = is_led_suspend_mode_supported()

IS_ALLY_LED_SUPPORTED = os.path.exists(ALLY_LED_PATH)


# AYANEO_EC_SUPPORT_LIST = [
#     "AIR",
#     "AIR Pro",
#     "AIR 1S",
#     "AIR 1S Limited",
#     "AYANEO 2",
#     "AYANEO 2S",
#     "GEEK",
#     "GEEK 1S",
# ]

# IS_AYANEO_EC_SUPPORTED = PRODUCT_NAME in AYANEO_EC_SUPPORT_LIST

API_URL = "https://api.github.com/repos/honjow/HueSync/releases/latest"


DEFAULT_BRIGHTNESS = 100
