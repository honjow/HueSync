import os

from config import (
    IS_ALLY_LED_SUPPORTED,
    IS_LED_SUPPORTED,
    LED_SUSPEND_MODE_PATH,
    PRODUCT_NAME,
    SYS_VENDOR,
    logger,
)
from devices.asus import AsusLEDDevice
from devices.asus_ally import AllyLEDDevice
from devices.ayaneo import AyaNeoLEDDevice
from devices.generic import GenericLEDDevice
from devices.gpd import GPDLEDDevice
from devices.led_device import LEDDevice
from devices.legion_go import LegionGoLEDDevice
from devices.msi import MSILEDDevice
from devices.onexplayer import OneXLEDDevice
from utils import Color, RGBMode, RGBModeCapabilities


class LedControl:
    """
    LedControl is responsible for managing LED device operations such as setting color, mode, and suspend mode.
    It selects the appropriate device based on system vendor and product information.

    LedControl负责管理LED设备的操作，例如设置颜色、模式和挂起模式。
    它根据系统供应商和产品信息选择合适的设备。
    """

    def __init__(self):
        """
        Initializes the LedControl by selecting the appropriate LED device.

        通过选择合适的LED设备来初始化LedControl。
        """
        self.device = self._get_device()

    def _get_device(self) -> LEDDevice:
        """
        Determines and returns the appropriate LEDDevice instance based on system configuration.

        根据系统配置确定并返回合适的LEDDevice实例。

        Returns:
            LEDDevice: An instance of a specific LED device class.
            LEDDevice: 特定LED设备类的实例。

        Raises:
            ValueError: If the device is unsupported.
            ValueError: 如果设备不受支持。
        """
        logger.info(f"SYS_VENDOR: {SYS_VENDOR}")
        logger.info(f"PRODUCT_NAME: {PRODUCT_NAME}")

        if IS_LED_SUPPORTED:
            logger.info("Using generic LED device")
            return GenericLEDDevice()
        elif IS_ALLY_LED_SUPPORTED:
            logger.info("Using Ally LED device")
            return AllyLEDDevice()
        elif SYS_VENDOR == "AYANEO":
            logger.info("Using AyaNeo LED device")
            return AyaNeoLEDDevice()
        elif SYS_VENDOR == "GPD" and (PRODUCT_NAME == "G1618-04"):
            logger.info("Using GPD LED device")
            return GPDLEDDevice()
        elif (
            SYS_VENDOR == "ONE-NETBOOK"
            or SYS_VENDOR == "ONE-NETBOOK TECHNOLOGY CO., LTD."
            or SYS_VENDOR == "AOKZOE"
        ):
            logger.info("Using OneX LED device")
            return OneXLEDDevice()
        elif SYS_VENDOR == "ASUSTeK COMPUTER INC.":
            logger.info("Using Asus LED device")
            return AsusLEDDevice()
        elif SYS_VENDOR == "LENOVO":
            logger.info("Using Legion Go LED device")
            return LegionGoLEDDevice()
        elif SYS_VENDOR == "Micro-Star International Co., Ltd.":
            logger.info("Using MSI LED device")
            return MSILEDDevice()
        logger.error("Unsupported device")
        raise ValueError("Unsupported device")

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
    ) -> None:
        """
        Set the color of the LED
        """
        self.device.set_color(
            mode or RGBMode.Solid,
            color,
            color2,
            init=init,
            brightness=brightness,
            speed=speed,
        )

    def get_suspend_mode(self) -> str | None:
        """
        Retrieves the current suspend mode from the LED device if supported.

        如果支持，从LED设备检索当前的挂起模式。

        Returns:
            str: The current suspend mode, or an empty string if not supported.
            str: 当前的挂起模式，如果不支持则为空字符串。
        """
        if IS_LED_SUPPORTED:
            if os.path.exists(LED_SUSPEND_MODE_PATH):
                with open(LED_SUSPEND_MODE_PATH, "r") as f:
                    # eg: [oem] keep off, read the part between []
                    return f.read().split("[")[1].split("]")[0]
        else:
            return self.device.get_suspend_mode()

    def set_suspend_mode(self, mode: str) -> None:
        """
        Sets the suspend mode for the LED device if supported.

        如果支持，为LED设备设置挂起模式。

        Args:
            mode (str): The suspend mode to set.
            mode (str): 要设置的挂起模式。
        """
        if IS_LED_SUPPORTED:
            if os.path.exists(LED_SUSPEND_MODE_PATH):
                with open(LED_SUSPEND_MODE_PATH, "w") as f:
                    f.write(f"{mode}")
        else:
            self.device.set_suspend_mode(mode)

    def suspend(self) -> None:
        self.device.suspend()

    def resume(self) -> None:
        self.device.resume()

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode.
        获取每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
                Each capability describes what features (color, brightness, etc.) are supported by the mode.
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
                每个功能支持情况描述该模式支持的特性（颜色、亮度等）。
        """
        return self.device.get_mode_capabilities()
