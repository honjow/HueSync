import os

from config import ALLY_LED_PATH, DEFAULT_BRIGHTNESS, logger
from utils import Color, RGBMode

from .asus import AsusLEDDevice


class AllyLEDDevice(AsusLEDDevice):
    """
    AllyLEDDevice provides control functionalities specific to Ally LED devices,
    including color and mode adjustments.

    AllyLEDDevice提供Ally LED设备特有的控制功能，包括颜色和模式调整。
    """

    def _set_solid_color(self, color: Color) -> None:
        self._set_color_by_sysfs(color)

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
    ) -> None:
        if not color:
            return
        if mode == RGBMode.Solid:
            self._set_color_by_sysfs(color)
        else:
            super().set_color(mode, color, color2, init, brightness=brightness, speed=speed)

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
