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
from led.ausu_led_device_hid import AsusLEDDeviceHID
from led.onex_led_device_hid import OneXLEDDeviceHID
from led.onex_led_device_serial import OneXLEDDeviceSerial
from led_device import BaseLEDDevice, LEDDevice
from utils import AyaJoystickGroup, AyaLedZone, Color, RGBMode, RGBModeCapabilities
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
        elif SYS_VENDOR == "GPD" and (PRODUCT_NAME == "G1618-04"):
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

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        """
        Set the color of the LED
        """
        if mode == RGBMode.Disabled:
            black = Color(0, 0, 0)
            self.device.set_color(
                RGBMode.Solid,
                black,
                black,
            )
        else:
            self.device.set_color(
                mode or RGBMode.Solid,
                color,
                color2,
            )

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


class GenericLEDDevice(BaseLEDDevice):
    """
    GenericLEDDevice serves as a base class for LED devices, providing basic functionality
    for setting color and brightness.

    GenericLEDDevice作为LED设备的基类，提供设置颜色和亮度的基本功能。
    """

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        if os.path.exists(LED_PATH):
            with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                _brightness: int = DEFAULT_BRIGHTNESS * 255 // 100
                logger.debug(f"brightness={_brightness}")
                f.write(str(_brightness))
            with open(os.path.join(LED_PATH, "multi_intensity"), "w") as f:
                f.write(f"{color.R} {color.G} {color.B}")


class GPDLEDDevice(BaseLEDDevice):
    """
    GPDLEDDevice is tailored for GPD devices, allowing specific control over
    color and mode settings.

    GPDLEDDevice专为GPD设备设计，允许对颜色和模式设置进行特定控制。
    """

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        try:
            wc = WinControls(disableFwCheck=True)
            _color = Color(
                color.R * DEFAULT_BRIGHTNESS // 100,
                color.G * DEFAULT_BRIGHTNESS // 100,
                color.B * DEFAULT_BRIGHTNESS // 100,
            )
            ledmode = "solid"
            match mode:
                case RGBMode.Solid:
                    ledmode = "solid"
                case RGBMode.Disabled:
                    ledmode = "off"
                case RGBMode.Pulse:
                    ledmode = "breathe"
                case RGBMode.Spiral:
                    ledmode = "rotate"

            conf = [f"ledmode={ledmode}", f"colour={_color.hex()}"]
            logger.info(f"conf={conf}")
            if wc.setConfig(config=conf):
                wc.writeConfig()

        except Exception as e:
            logger.error(e, exc_info=True)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Default mode capabilities.
        默认模式功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        return {
            RGBMode.Disabled: RGBModeCapabilities(
                mode=RGBMode.Disabled,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
        }


class AyaNeoLEDDevice(BaseLEDDevice):
    """
    AyaNeoLEDDevice offers advanced control for AyaNeo devices, supporting pixel-level
    adjustments and various modes.

    AyaNeoLEDDevice为AyaNeo设备提供高级控制，支持像素级调整和各种模式。
    """

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        if not IS_AYANEO_EC_SUPPORTED:
            return
        self.set_color_all(color)

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

    def set_color_all(self, color: Color) -> None:
        color = Color(
            color.R * DEFAULT_BRIGHTNESS // 100,
            color.G * DEFAULT_BRIGHTNESS // 100,
            color.B * DEFAULT_BRIGHTNESS // 100,
        )

        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Right, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Bottom, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Left, color)
        self.set_color_one(AyaJoystickGroup.ALL, AyaLedZone.Top, color)


class OneXLEDDevice(BaseLEDDevice):
    """
    OneXLEDDevice is designed for OneX devices, enabling HID and serial communication
    for color and mode settings.

    OneXLEDDevice专为OneX设备设计，支持HID和串行通信以进行颜色和模式设置。
    """

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        if "ONEXPLAYER X1" in PRODUCT_NAME:
            self.set_onex_color_serial(color)
        else:
            self.set_onex_color_hid(color)

    def set_onex_color_hid(self, color: Color) -> None:
        max_retries = 3
        retry_delay = 1  # seconds
        for retry in range(max_retries + 1):
            if retry > 0:
                logger.info(f"Retry attempt {retry}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避

            ledDevice = OneXLEDDeviceHID(0x1A2C, 0xB001)
            if ledDevice.is_ready():
                logger.info(f"set_onex_color: color={color}")
                ledDevice.set_led_color(color, RGBMode.Solid)
                return
            logger.info("set_onex_color_hid: device not ready")

        logger.warning("Failed to set color after all retries")

    def set_onex_color_serial(self, color: Color) -> None:
        try:
            ledDevice = OneXLEDDeviceSerial()
            if ledDevice.is_ready():
                logger.info(f"set_onex_color: color={color}")
                ledDevice.set_led_color(color, RGBMode.Solid)
        except Exception as e:
            logger.error(e, exc_info=True)


class AsusLEDDevice(BaseLEDDevice):
    """
    AsusLEDDevice provides control for Asus devices, integrating with specific
    product IDs for tailored settings.

    AsusLEDDevice为Asus设备提供控制，集成特定产品ID以进行定制设置。
    """

    def __init__(self):
        super().__init__()
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                self.id_info = id_info

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        try:
            ledDevice = AsusLEDDeviceHID(
                self.id_info.vid, self.id_info.pid, [0xFF31], [0x0080]
            )
            if ledDevice.is_ready():
                init = self._current_mode != mode
                logger.info(f"set_asus_color: color={color} mode={mode} init={init}")
                if mode:
                    ledDevice.set_led_color(color, mode, init=init)
                    self._current_mode = mode
                return
            logger.info("set_asus_color: device not ready")
        except Exception as e:
            logger.error(e, exc_info=True)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for Asus devices.
        获取 Asus 设备每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping RGB modes to their capabilities.
        """
        return {
            RGBMode.Disabled: RGBModeCapabilities(
                mode=RGBMode.Disabled,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                supports_color=False,
                supports_color2=False,
                supports_speed=True,
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                supports_color=True,
                supports_color2=False,
                supports_speed=True,
            ),
            # RGBMode.Duality: RGBModeCapabilities(
            #     mode=RGBMode.Duality,
            #     supports_color=True,
            #     supports_color2=True,
            #     supports_speed=True,
            # ),
        }


class AllyLEDDevice(AsusLEDDevice):
    """
    AllyLEDDevice provides control functionalities specific to Ally LED devices,
    including color and mode adjustments.

    AllyLEDDevice提供Ally LED设备特有的控制功能，包括颜色和模式调整。
    """

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return
        if mode == RGBMode.Solid:
            self._set_color_by_sysfs(color)
        else:
            super().set_color(mode, color, color2)

    def _set_color_by_sysfs(
        self,
        color: Color,
    ) -> None:
        if not color:
            return
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
                _brightness: int = DEFAULT_BRIGHTNESS * 255 // 100
                logger.debug(f"ally brightness={_brightness}")
                f.write(str(_brightness))
