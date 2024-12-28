import os
import time

from config import (
    ALLY_LED_PATH,
    DEFAULT_BRIGHTNESS,
    IS_ALLY_LED_SUPPORTED,
    IS_AYANEO_EC_SUPPORTED,
    IS_LED_SUPPORTED,
    LED_PATH,
    LED_SUSPEND_MODE_PATH,
    PRODUCT_NAME,
    SYS_VENDOR,
    logger,
)
from ec import EC
from id_info import ID_MAP
from led.onex_led_device_serial import OneXLEDDeviceSerial
from led_device import LEDDevice
from led.ausu_led_device_hid import AsusLEDDeviceHID
from led.onex_led_device_hid import OneXLEDDeviceHID
from utils import AyaJoystickGroup, AyaLedZone, Color, LEDLevel
from wincontrols.hardware import WinControls


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
        if IS_LED_SUPPORTED:
            return GenericLEDDevice()
        elif IS_ALLY_LED_SUPPORTED:
            return AllyLEDDevice()
        elif IS_AYANEO_EC_SUPPORTED:
            return AyaNeoLEDDevice()
        elif SYS_VENDOR == "GPD" and PRODUCT_NAME == "G1618-04":
            return GPDLEDDevice()
        elif (
            SYS_VENDOR == "ONE-NETBOOK"
            or SYS_VENDOR == "ONE-NETBOOK TECHNOLOGY CO., LTD."
            or SYS_VENDOR == "AOKZOE"
        ):
            return OneXLEDDevice()
        elif SYS_VENDOR == "ASUSTeK COMPUTER INC.":
            return AsusLEDDevice()
        raise ValueError("Unsupported device")

    def set_Color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        """
        Sets the color and brightness of the LED device.

        设置LED设备的颜色和亮度。

        Args:
            color (Color): The color to set on the LED device.
            color (Color): 要在LED设备上设置的颜色。
            brightness (int): The brightness level, default is DEFAULT_BRIGHTNESS.
            brightness (int): 亮度级别，默认值为DEFAULT_BRIGHTNESS。
        """
        self.device.set_color(color, brightness)

    def set_mode(self, mode: str):
        """
        Sets the mode of the LED device.

        设置LED设备的模式。

        Args:
            mode (str): The mode to set on the LED device.
            mode (str): 要在LED设备上设置的模式。
        """
        self.device.set_mode(mode)

    def get_suspend_mode(self) -> str:
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
        return ""

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


class GenericLEDDevice(LEDDevice):
    """
    GenericLEDDevice serves as a base class for LED devices, providing basic functionality
    for setting color and brightness.

    GenericLEDDevice作为LED设备的基类，提供设置颜色和亮度的基本功能。
    """

    def set_color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        if os.path.exists(LED_PATH):
            with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                _brightness: int = brightness * 255 // 100
                logger.debug(f"brightness={_brightness}")
                f.write(str(_brightness))
            with open(os.path.join(LED_PATH, "multi_intensity"), "w") as f:
                f.write(f"{color.R} {color.G} {color.B}")

    def set_mode(self, mode: str):
        pass


class GPDLEDDevice(LEDDevice):
    """
    GPDLEDDevice is tailored for GPD devices, allowing specific control over
    color and mode settings.

    GPDLEDDevice专为GPD设备设计，允许对颜色和模式设置进行特定控制。
    """

    def set_color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        logger.info(f"SYS_VENDOR={SYS_VENDOR}, PRODUCT_NAME={PRODUCT_NAME}")
        try:
            wc = WinControls(disableFwCheck=True)
            color = Color(
                color.R * brightness // 100,
                color.G * brightness // 100,
                color.B * brightness // 100,
            )
            conf = ["ledmode=solid", f"colour={color.hex()}"]
            logger.info(f"conf={conf}")
            if wc.loaded and wc.setConfig(conf):
                wc.writeConfig()
        except Exception as e:
            logger.error(e, exc_info=True)

    def set_mode(self, mode: str):
        pass


class AllyLEDDevice(LEDDevice):
    """
    AllyLEDDevice provides control functionalities specific to Ally LED devices,
    including color and mode adjustments.

    AllyLEDDevice提供Ally LED设备特有的控制功能，包括颜色和模式调整。
    """

    def set_color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        # read /sys/class/leds/ally:rgb:joystick_rings/multi_index
        multi_index = ""
        if os.path.exists(os.path.join(ALLY_LED_PATH, "multi_index")):
            with open(os.path.join(ALLY_LED_PATH, "multi_index"), "r") as f:
                multi_index = f.read().strip()
                logger.debug(f"ally multi_index={multi_index}")

        count = len(multi_index.split(" "))
        if count == 12:
            # set /sys/class/leds/ally:rgb:joystick_rings/multi_intensity
            with open(os.path.join(ALLY_LED_PATH, "multi_intensity"), "w") as f:
                f.write(
                    f"{color.R} {color.G} {color.B} {color.R} {color.G} {color.B} {color.R} {color.G} {color.B} {color.R} {color.G} {color.B}"
                )
        elif count == 4:
            color_hex = color.hex()
            # set /sys/class/leds/ally:rgb:joystick_rings/multi_intensity
            with open(os.path.join(ALLY_LED_PATH, "multi_intensity"), "w") as f:
                f.write(f"0x{color_hex} 0x{color_hex} 0x{color_hex} 0x{color_hex}")

        if os.path.exists(os.path.join(ALLY_LED_PATH, "brightness")):
            with open(os.path.join(ALLY_LED_PATH, "brightness"), "w") as f:
                _brightness: int = brightness * 255 // 100
                logger.debug(f"ally brightness={_brightness}")
                f.write(str(_brightness))

    def set_mode(self, mode: str):
        pass


class AyaNeoLEDDevice(LEDDevice):
    """
    AyaNeoLEDDevice offers advanced control for AyaNeo devices, supporting pixel-level
    adjustments and various modes.

    AyaNeoLEDDevice为AyaNeo设备提供高级控制，支持像素级调整和各种模式。
    """

    def set_color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        if os.path.exists(os.path.join(LED_PATH, "brightness")):
            with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                _brightness: int = brightness * 255 // 100
                logger.debug(f"brightness={_brightness}")
                f.write(str(_brightness))
        self.set_color_all(color, brightness)

    def set_color_one(self, group: int, ledZone: int, color: Color) -> None:
        self.set_aya_subpixel(group, ledZone * 3, color.R)
        self.set_aya_subpixel(group, ledZone * 3 + 1, color.G)
        self.set_aya_subpixel(group, ledZone * 3 + 2, color.B)

    def set_aya_subpixel(self, group: int, subpixel_idx: int, brightness: int) -> None:
        logger.debug(
            f"group={group} subpixel_idx={subpixel_idx},brightness={brightness}"
        )
        self.aya_ec_cmd(group, subpixel_idx, brightness)

    def aya_ec_cmd(self, group: int, command: int, argument: int) -> None:
        for x in range(2):
            EC.Write(0x6D, group)
            EC.Write(0xB1, command)
            EC.Write(0xB2, argument)
            EC.Write(0xBF, 0x10)
            time.sleep(0.005)
            # EC.Write(0xBF, 0xFF)
            EC.Write(0xBF, 0xFE)

    def set_color_all(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        color = Color(
            color.R * brightness // 100,
            color.G * brightness // 100,
            color.B * brightness // 100,
        )

        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Right, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Bottom, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Left, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Top, color)

    def set_mode(self, mode: str):
        pass


class OneXLEDDevice(LEDDevice):
    """
    OneXLEDDevice is designed for OneX devices, enabling HID and serial communication
    for color and mode settings.

    OneXLEDDevice专为OneX设备设计，支持HID和串行通信以进行颜色和模式设置。
    """

    def set_color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        if "ONEXPLAYER X1" in PRODUCT_NAME:
            self.set_onex_color_serial(color, brightness)
        else:
            self.set_onex_color_hid(color, brightness)

    def set_onex_color_hid(
        self, color: Color, brightness: int = DEFAULT_BRIGHTNESS
    ) -> None:
        ledDevice = OneXLEDDeviceHID(0x1A2C, 0xB001)
        # _brightness: int = int(
        #     round((299 * color.R + 587 * color.G + 114 * color.B) / 1000 / 255.0 * 100)
        # )
        if ledDevice.is_ready():
            logger.info(f"set_onex_color: color={color}, brightness={brightness}")
            ledDevice.set_led_brightness(brightness)
            ledDevice.set_led_color(color, LEDLevel.SolidColor)

    def set_onex_color_serial(
        self, color: Color, brightness: int = DEFAULT_BRIGHTNESS
    ) -> None:
        try:
            ledDevice = OneXLEDDeviceSerial()
            if ledDevice.is_ready():
                logger.info(f"set_onex_color_serial: color={color}")
                ledDevice.set_led_brightness(brightness)
                ledDevice.set_led_color(color, LEDLevel.SolidColor)
        except Exception as e:
            logger.error(e, exc_info=True)

    def set_mode(self, mode: str):
        pass


class AsusLEDDevice(LEDDevice):
    """
    AsusLEDDevice provides control for Asus devices, integrating with specific
    product IDs for tailored settings.

    AsusLEDDevice为Asus设备提供控制，集成特定产品ID以进行定制设置。
    """

    def __init__(self):
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                self.id_info = id_info

    def set_color(self, color: Color, brightness: int = DEFAULT_BRIGHTNESS) -> None:
        ledDevice = AsusLEDDeviceHID(
            self.id_info.vid, self.id_info.pid, [0xFF31], [0x0080]
        )
        if ledDevice.is_ready():
            logger.info(f"set_asus_color: color={color}, brightness={brightness}")
            ledDevice.set_led_color(color, brightness, LEDLevel.SolidColor)

    def set_mode(self, mode: str):
        pass
