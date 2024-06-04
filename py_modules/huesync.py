import os
from config import (
    logger,
    LED_PATH,
    IS_LED_SUPPORTED,
    IS_AYANEO_EC_SUPPORTED,
    SYS_VENDOR,
    PRODUCT_NAME,
    LED_MODE_PATH,
    LED_SUSPEND_MODE_PATH,
)
from ec import EC
from led.onex_led_device import OneXLEDDevice
from led.onex_led_device_serial import OneXLEDDeviceSerial
from utils import AyaJoystick, AyaLedPosition, Color, LEDLevel
from wincontrols.hardware import WinControls


class LedControl:
    def set_Color(self, color: Color, brightness: int = 100):
        logger.info(f"SYS_VENDOR={SYS_VENDOR}, PRODUCT_NAME={PRODUCT_NAME}")
        if IS_LED_SUPPORTED:
            if os.path.exists(LED_MODE_PATH):
                with open(LED_MODE_PATH, "w") as f:
                    f.write("1")

            for x in range(2):
                with open(os.path.join(LED_PATH, "brightness"), "w") as f:
                    _brightness: int = brightness * 255 // 100
                    logger.debug(f"brightness={_brightness}")
                    f.write(str(_brightness))
                with open(os.path.join(LED_PATH, "multi_intensity"), "w") as f:
                    f.write(f"{color.R} {color.G} {color.B}")
                # time.sleep(0.01)
        elif IS_AYANEO_EC_SUPPORTED:
            self.set_aya_all_pixels(color, brightness)
        elif SYS_VENDOR == "GPD" and PRODUCT_NAME == "G1618-04":
            self.set_gpd_color(color, brightness)
        elif (
            SYS_VENDOR == "ONE-NETBOOK"
            or SYS_VENDOR == "ONE-NETBOOK TECHNOLOGY CO., LTD."
            or SYS_VENDOR == "AOKZOE"
        ):
            logger.info(f"onxplayer color={color}")
            self.set_onex_color(color, brightness)

    def set_gpd_color(self, color: Color, brightness: int = 100):
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

    def set_onex_color_hid(self, color: Color, brightness: int = 100):
        ledDevice = OneXLEDDevice(0x1A2C, 0xB001)
        # ledDevice = OneXLEDDevice(0x2f24, 0x135)
        # _brightness: int = int(
        #     round((299 * color.R + 587 * color.G + 114 * color.B) / 1000 / 255.0 * 100)
        # )
        if ledDevice.is_ready():
            logger.info(f"set_onex_color: color={color}, brightness={brightness}")
            ledDevice.set_led_brightness(brightness)
            ledDevice.set_led_color(color, color, LEDLevel.SolidColor)

    def set_onex_color_serial(self, color: Color, brightness: int = 100):
        ledDevice = OneXLEDDeviceSerial()
        if ledDevice.is_ready():
            logger.info(f"set_onex_color_serial: color={color}")
            ledDevice.set_led_brightness(brightness)
            ledDevice.set_led_color(color, color, LEDLevel.SolidColor)

    def set_onex_color(self, color: Color, brightness: int = 100):
        if "ONE-NETBOOK ONEXPLAYER X1" in PRODUCT_NAME:
            self.set_onex_color_serial(color, brightness)
        else:
            self.set_onex_color_hid(color, brightness)

    def get_suspend_mode(self):
        if IS_LED_SUPPORTED:
            if os.path.exists(LED_SUSPEND_MODE_PATH):
                with open(LED_SUSPEND_MODE_PATH, "r") as f:
                    # eg: [oem] keep off, read the part between []
                    return f.read().split("[")[1].split("]")[0]
        return ""

    def set_suspend_mode(self, mode: str):
        if IS_LED_SUPPORTED:
            if os.path.exists(LED_SUSPEND_MODE_PATH):
                with open(LED_SUSPEND_MODE_PATH, "w") as f:
                    f.write(f"{mode}")

    def set_aya_all_pixels(self, color: Color, brightness: int = 100):

        color = Color(
            color.R * brightness // 100,
            color.G * brightness // 100,
            color.B * brightness // 100,
        )

        self.set_aya_pixel(AyaJoystick.ALL, AyaLedPosition.Right, color)
        self.set_aya_pixel(AyaJoystick.ALL, AyaLedPosition.Bottom, color)
        self.set_aya_pixel(AyaJoystick.ALL, AyaLedPosition.Left, color)
        self.set_aya_pixel(AyaJoystick.ALL, AyaLedPosition.Top, color)

    def set_aya_pixel(self, js, led, color: Color):
        self.set_aya_subpixel(js, led * 3, color.R)
        self.set_aya_subpixel(js, led * 3 + 1, color.G)
        self.set_aya_subpixel(js, led * 3 + 2, color.B)

    def set_aya_subpixel(self, js, subpixel_idx, brightness):
        logger.debug(f"js={js} subpixel_idx={subpixel_idx},brightness={brightness}")
        self.aya_ec_cmd(js, subpixel_idx, brightness)

    def aya_ec_cmd(self, cmd, p1, p2):
        for x in range(2):
            EC.Write(0x6D, cmd)
            EC.Write(0xB1, p1)
            EC.Write(0xB2, p2)
            EC.Write(0xBF, 0x10)
            # time.sleep(0.01)
            EC.Write(0xBF, 0xFF)
            # time.sleep(0.01)
