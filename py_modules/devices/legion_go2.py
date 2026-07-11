import os
from typing import Optional

from config import logger
from utils import Color

from .generic import GenericLEDDevice
from .legion_power_led_mixin import LegionPowerLEDMixin

# The kernel multicolor LED-class device exposed by the hid-lenovo-go driver
# for the Legion Go 2 controller joystick rings.
GO2_LED_PATH = "/sys/class/leds/go:rgb:joystick_rings"


class LegionGo2LEDDevice(LegionPowerLEDMixin, GenericLEDDevice):
    """
    RGB control for the Lenovo Legion Go 2 via the in-kernel ``hid-lenovo-go``
    driver, which exposes the joystick-ring RGB as the multicolor LED-class
    device ``/sys/class/leds/go:rgb:joystick_rings``.

    On kernels with this driver the raw vendor HID interface is claimed by the
    driver (and hidden by InputPlumber), so the HID path used by
    ``LegionGoTabletLEDDevice`` cannot open the device. This class drives the
    sysfs LED instead. The go ring only lights when its ``enabled`` attribute is
    ``true`` (the generic sysfs mixin never writes it), and it also needs
    ``mode=custom`` / ``effect=monocolor`` for a static color, so
    ``_set_color_by_sysfs`` is overridden to handle those.

    Power LED control is inherited from ``LegionPowerLEDMixin`` using the same EC
    field as the Legion Go tablet device (LEDP, offset 0x52 bit 5).

    通过内核 hid-lenovo-go 驱动为 Lenovo Legion Go 2 提供 RGB 控制。
    """

    # Substring keywords for SysfsLEDMixin._detect_sysfs_led_path().
    SYSFS_LED_PATHS = ["go:rgb:joystick_rings", "joystick_rings"]

    # Power LED: same EC field as the Legion Go tablet (LEDP, offset 0x52 bit 5)
    POWER_LED_OFFSET = 0x52
    POWER_LED_BIT = 5

    def __init__(self):
        super().__init__()
        # Cache of last-written static attributes so software animation effects
        # (which call _set_solid_color per frame) don't re-write mode/effect/
        # enabled/brightness every frame and flood the controller.
        self._sysfs_cache: dict[str, str] = {}
        self._max_brightness_val: Optional[int] = None

    def _write_attr(self, attr: str, value: str) -> None:
        if not self._sysfs_led_path:
            return
        path = os.path.join(self._sysfs_led_path, attr)
        if os.path.exists(path):
            with open(path, "w") as f:
                f.write(value)

    def _write_if_changed(self, attr: str, value: str) -> None:
        if self._sysfs_cache.get(attr) == value:
            return
        self._write_attr(attr, value)
        self._sysfs_cache[attr] = value

    def _get_max_brightness(self) -> int:
        if self._max_brightness_val is None:
            self._max_brightness_val = 100
            if self._sysfs_led_path:
                mb_path = os.path.join(self._sysfs_led_path, "max_brightness")
                try:
                    if os.path.exists(mb_path):
                        with open(mb_path) as f:
                            self._max_brightness_val = int(f.read().strip())
                except Exception:
                    pass
        return self._max_brightness_val

    def _set_color_by_sysfs(
        self, color: Color, brightness: Optional[int] = None
    ) -> bool:
        """
        Set a solid color on the go ring. Overrides SysfsLEDMixin to also write
        the go-specific ``mode``/``effect``/``enabled`` attributes and to clamp
        brightness to the device's ``max_brightness`` (the ring is 0-100, not
        the 0-255 the generic mixin assumes).
        """
        if not self._sysfs_led_path and not self._detect_sysfs_led_path():
            logger.debug("No go:rgb sysfs LED path available")
            return False

        try:
            is_off = color.R == 0 and color.G == 0 and color.B == 0
            max_b = self._get_max_brightness()
            bval = max_b if brightness is None else max(0, min(max_b, int(brightness)))

            # Static attributes: write only when they change.
            self._write_if_changed("mode", "custom")
            self._write_if_changed("effect", "monocolor")
            self._write_if_changed("brightness", str(bval))
            # The ring is dark unless 'enabled' is true; a black color means off.
            self._write_if_changed("enabled", "false" if is_off else "true")

            # Color changes per frame for software effects, so always write it.
            self._write_attr("multi_intensity", f"{color.R} {color.G} {color.B}")

            logger.debug(
                f"go:rgb set color=({color.R},{color.G},{color.B}) "
                f"brightness={bval} off={is_off}"
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to set go:rgb color via sysfs: {e}")
            return False
