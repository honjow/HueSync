import os

from config import (
    DEFAULT_BRIGHTNESS,
    LED_PATH,
    logger,
)


from .led_device import BaseLEDDevice
from utils import Color, RGBMode


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
