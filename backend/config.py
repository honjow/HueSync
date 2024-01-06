import logging

#日志配置
try:
    LOG_LOCATION = "/tmp/ayaled_py.log"
    logging.basicConfig(
        level = logging.DEBUG,
        filename = LOG_LOCATION,
        format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s",
        filemode = 'w',
        force = True)
except Exception as e:
    logging.error(f"日志配置异常|{e}")

#设备信息获取配置
try:
    PRODUCT_NAME = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
except Exception as e:
    logging.error(f"设备信息配置异常|{e}")

#灯效ec偏移配置
try:
    if PRODUCT_NAME in (
        "AIR",
        "AIR Pro",
        "AIR 1S"
        "AYANEO 2",
        "AYANEO 2S",
        "AYANEO GEEK",
        "AYANEO GEEK 1S",
        "SLIDE",
        ):
        FAN_MANUAL_OFFSET=0x4a
        FAN_RPMWRITE_OFFSET=0x4b
        FAN_RPMREAD_OFFSET=0x76
        FAN_RPMWRITE_MAX=100
        FAN_IS_ADAPTED=True
except Exception as e:
    logging.error(f"灯效ec配置异常|{e}")
