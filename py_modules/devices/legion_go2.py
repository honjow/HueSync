import os
from typing import Optional

from config import logger
from utils import Color, RGBMode, RGBModeCapabilities

from .generic import GenericLEDDevice
from .legion_power_led_mixin import LegionPowerLEDMixin

# The kernel multicolor LED-class device exposed by the hid-lenovo-go driver
# for the Legion Go 2 controller joystick rings.
GO2_LED_PATH = "/sys/class/leds/go:rgb:joystick_rings"

# hid-lenovo-go exposes the firmware effects with kernel-facing names. HueSync's
# Rainbow mode is the firmware's dynamic/chroma effect, while Spiral is the
# firmware's rotating rainbow effect.
GO2_EFFECTS = {
    RGBMode.Rainbow: "chroma",
    RGBMode.Spiral: "rainbow",
}

GO2_SPEEDS = {
    "low": 33,
    "medium": 66,
    "high": 100,
}


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
        self._multi_max_intensity_val: Optional[tuple[int, int, int]] = None

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [mode for mode in GO2_EFFECTS if self._has_native_effect(mode)]

    def _has_writable_sysfs_attr(self, attr: str) -> bool:
        if not self._sysfs_led_path:
            return False
        path = os.path.join(self._sysfs_led_path, attr)
        return os.path.exists(path) and os.access(path, os.W_OK)

    def _get_index_values(self, attr: str) -> set[str]:
        if not self._sysfs_led_path:
            return set()
        path = os.path.join(self._sysfs_led_path, attr)
        try:
            with open(path) as f:
                return set(f.read().split())
        except Exception:
            return set()

    def _get_supported_effects(self) -> set[str]:
        return self._get_index_values("effect_index")

    def _has_native_effect(self, mode: RGBMode) -> bool:
        effect = GO2_EFFECTS.get(mode)
        if effect not in self._get_supported_effects():
            return False
        if "custom" not in self._get_index_values("mode_index"):
            return False

        required_attrs = {
            "profile",
            "mode",
            "effect",
            "brightness",
            "enabled",
            "multi_intensity",
            "speed",
        }
        return all(
            self._has_writable_sysfs_attr(attr) for attr in required_attrs
        )

    def _write_attr(self, attr: str, value: str) -> bool:
        if not self._sysfs_led_path:
            return False
        path = os.path.join(self._sysfs_led_path, attr)
        if not os.path.exists(path):
            return False
        with open(path, "w") as f:
            f.write(value)
        return True

    def _write_if_changed(self, attr: str, value: str) -> bool:
        if self._sysfs_cache.get(attr) == value:
            return self._has_writable_sysfs_attr(attr)
        if not self._write_attr(attr, value):
            return False
        self._sysfs_cache[attr] = value
        return True

    def _write_state_attr(self, attr: str, value: str) -> None:
        """Write an attribute unconditionally when applying a native effect."""
        if not self._write_attr(attr, value):
            raise RuntimeError(f"go:rgb {attr} attribute is unavailable")
        # Keep the software-effect cache aligned with the state just written.
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

    def _get_multi_max_intensity(self) -> tuple[int, int, int]:
        if self._multi_max_intensity_val is None:
            fallback = self._get_max_brightness()
            self._multi_max_intensity_val = (fallback, fallback, fallback)
            if self._sysfs_led_path:
                path = os.path.join(
                    self._sysfs_led_path, "multi_max_intensity"
                )
                try:
                    if os.path.exists(path):
                        with open(path) as f:
                            values = [int(value) for value in f.read().split()]
                        if len(values) >= 3 and all(
                            value >= 0 for value in values[:3]
                        ):
                            self._multi_max_intensity_val = tuple(values[:3])
                except Exception:
                    pass
        return self._multi_max_intensity_val

    def _color_to_sysfs(self, color: Color) -> str:
        channels = (color.R, color.G, color.B)
        values = (
            round(channel * maximum / 255)
            for channel, maximum in zip(
                channels, self._get_multi_max_intensity()
            )
        )
        return " ".join(str(value) for value in values)

    def _brightness_to_sysfs(self, brightness: Optional[int]) -> int:
        """Convert a HueSync percentage to the LED class brightness range."""
        percent = 100 if brightness is None else max(0, min(100, int(brightness)))
        return round(self._get_max_brightness() * percent / 100)

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
        brightness: int | None = None,
        **kwargs,
    ) -> None:
        """Set a native hid-lenovo-go effect through its sysfs ABI."""
        if not color or not mode:
            return
        if not self._sysfs_led_path and not self._detect_sysfs_led_path():
            raise RuntimeError("No go:rgb sysfs LED path available")

        effect = GO2_EFFECTS.get(mode)
        if effect is None or not self._has_native_effect(mode):
            raise ValueError(f"Unsupported go:rgb hardware mode: {mode}")

        bval = self._brightness_to_sysfs(brightness)

        # Profile 3 matches the legacy HID backend. It must be selected before
        # any profile data is written because the kernel driver's initial
        # profile value is not a valid user profile.
        self._write_state_attr("profile", "3")
        self._write_state_attr("mode", "custom")
        self._write_state_attr(
            "speed", str(GO2_SPEEDS.get(speed or "medium", 66))
        )
        self._write_state_attr("multi_intensity", self._color_to_sysfs(color))
        self._write_state_attr("brightness", str(bval))
        self._write_state_attr("effect", effect)
        self._write_state_attr("enabled", "true")

        logger.debug(
            f"go:rgb set effect={effect} color=({color.R},{color.G},{color.B}) "
            f"brightness={bval} speed={speed}"
        )

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
            bval = self._brightness_to_sysfs(brightness)

            # Static attributes: write only when they change.
            required_writes = (
                self._write_if_changed("profile", "3"),
                self._write_if_changed("mode", "custom"),
                self._write_if_changed("effect", "monocolor"),
                self._write_if_changed("brightness", str(bval)),
            )
            # The ring is dark unless 'enabled' is true; a black color means off.
            enabled_written = self._write_if_changed(
                "enabled", "false" if is_off else "true"
            )

            # Color changes per frame for software effects, so always write it.
            color_written = self._write_attr(
                "multi_intensity", self._color_to_sysfs(color)
            )

            if (
                not all(required_writes)
                or not enabled_written
                or not color_written
            ):
                logger.warning("Incomplete go:rgb sysfs interface")
                return False

            logger.debug(
                f"go:rgb set color=({color.R},{color.G},{color.B}) "
                f"brightness={bval} off={is_off}"
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to set go:rgb color via sysfs: {e}")
            return False

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        capabilities = super().get_mode_capabilities()
        if self._has_native_effect(RGBMode.Rainbow):
            capabilities[RGBMode.Rainbow] = RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                color=False,
                speed=True,
                brightness=True,
            )
        if self._has_native_effect(RGBMode.Spiral):
            capabilities[RGBMode.Spiral] = RGBModeCapabilities(
                mode=RGBMode.Spiral,
                color=False,
                speed=True,
                brightness=True,
            )
        return capabilities
