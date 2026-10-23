import os
import time
from typing import Optional

from utils import Color, RGBMode, RGBModeCapabilities

from .generic import GenericLEDDevice

LED_ROOT = "/sys/class/leds"

ZONE_PRIMARY = "primary"
ZONE_SECONDARY = "secondary"
ZONE_REAR = "rear"

ZONE_DIRS = {
    ZONE_PRIMARY: "go:rgb:joystick_rings",
    ZONE_SECONDARY: "oxp:rgb:guide_button",
    ZONE_REAR: "oxp:rgb:rear_logo",
}

ZONE_NAME_KEYS = {
    ZONE_PRIMARY: "ZONE_PRIMARY_NAME",
    ZONE_SECONDARY: "ZONE_GUIDE_BUTTON_NAME",
    ZONE_REAR: "ZONE_REAR_LOGO_NAME",
}

REQUIRED_ZONE_ATTRS = ("brightness", "multi_intensity")

# Native OXP preset effects, keyed by HueSync mode. A preset is only advertised
# and accepted when its literal token is present in the ring effect_index.
OXP_EFFECTS = {
    RGBMode.OXP_MONSTER_WOKE: "monster_woke",
    RGBMode.OXP_FLOWING: "flowing_light",
    RGBMode.OXP_SUNSET: "sunset_afterglow",
    RGBMode.OXP_NEON: "neon",
    RGBMode.OXP_DREAMY: "dreamy",
    RGBMode.OXP_CYBERPUNK: "cyberpunk",
    RGBMode.OXP_COLORFUL: "colorful",
    RGBMode.OXP_AURORA: "aurora",
    RGBMode.OXP_SUN: "warm_sun",
}

OXP_CLASSIC_COLOR = Color(0xB7, 0x30, 0x00)

BRIGHTNESS_LEVELS = {
    "low": 33,
    "medium": 66,
    "high": 100,
}

SPEED_LEVELS = {
    "low": 0,
    "medium": 5,
    "high": 9,
}

SOFTWARE_MODES = frozenset(
    (
        RGBMode.Pulse,
        RGBMode.Rainbow,
        RGBMode.Duality,
        RGBMode.Gradient,
        RGBMode.Battery,
        RGBMode.Spiral,
    )
)

STATIC_BRIGHTNESS = 100


class OneXPlayer3LEDDevice(GenericLEDDevice):
    """
    RGB control for the ONEXPLAYER 3 through the hid-oxp sysfs LED-class nodes.

    The ring exposes a dedicated ``enabled`` attribute and the only speed
    control; the guide button and rear logo are independent static zones. The
    frontend already applies HSV brightness to static colors, so the sysfs
    brightness stays at maximum for static colors.
    """

    def __init__(self, led_root: str = LED_ROOT):
        self._led_root = led_root
        self._sysfs_cache: dict[tuple[str, str], str] = {}
        self._requested_colors: dict[str, Color] = {}
        self._zone_enabled: dict[str, bool] = {}
        self._available_zones: list[str] = []
        super().__init__()
        self._available_zones = [
            zone for zone in ZONE_DIRS if self._zone_is_available(zone)
        ]
        for zone in self._available_zones:
            self._zone_enabled[zone] = True

    @classmethod
    def is_available(cls, led_root: str = LED_ROOT) -> bool:
        """The ring's brightness and multi_intensity attributes are required."""
        primary = os.path.join(led_root, ZONE_DIRS[ZONE_PRIMARY])
        return all(
            os.path.exists(os.path.join(primary, attr))
            for attr in REQUIRED_ZONE_ATTRS
        )

    def _zone_path(self, zone: str) -> str:
        return os.path.join(self._led_root, ZONE_DIRS[zone])

    def _attr_path(self, zone: str, attr: str) -> str:
        return os.path.join(self._zone_path(zone), attr)

    def _detect_sysfs_led_path(self) -> Optional[str]:
        """Only look at the exact ring node under the configured root."""
        primary = self._zone_path(ZONE_PRIMARY)
        self._sysfs_led_path = primary if os.path.isdir(primary) else None
        return self._sysfs_led_path

    def _zone_is_available(self, zone: str) -> bool:
        return all(
            os.path.exists(self._attr_path(zone, attr))
            for attr in REQUIRED_ZONE_ATTRS
        )

    def _read_tokens(self, zone: str, attr: str) -> set[str]:
        try:
            with open(self._attr_path(zone, attr)) as f:
                return set(f.read().split())
        except OSError:
            return set()

    def _effect_tokens(self) -> set[str]:
        return self._read_tokens(ZONE_PRIMARY, "effect_index")

    def _primary_has(self, attr: str) -> bool:
        return os.path.exists(self._attr_path(ZONE_PRIMARY, attr))

    def _write_attr(self, zone: str, attr: str, value: str) -> None:
        with open(self._attr_path(zone, attr), "w") as f:
            f.write(str(value))

    def _write_cached(self, zone: str, attr: str, value: str) -> None:
        key = (zone, attr)
        value = str(value)
        if self._sysfs_cache.get(key) == value:
            return
        self._write_attr(zone, attr, value)
        self._sysfs_cache[key] = value

    @staticmethod
    def _color_to_sysfs(color: Color) -> str:
        return f"{color.R} {color.G} {color.B}"

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        modes = [RGBMode.Disabled, RGBMode.Solid]
        effects = self._effect_tokens()
        for mode, effect in OXP_EFFECTS.items():
            if effect in effects:
                modes.append(mode)
        if "monocolor" in effects:
            modes.append(RGBMode.OXP_CLASSIC)
        return modes

    def _write_zone_off(self, zone: str) -> None:
        self._write_cached(zone, "brightness", "0")
        if zone == ZONE_PRIMARY and self._primary_has("enabled"):
            self._write_cached(zone, "enabled", "false")
        self._write_attr(zone, "multi_intensity", "0 0 0")

    def _write_static_zone(self, zone: str, color: Color) -> None:
        self._write_cached(zone, "effect", "monocolor")
        self._write_cached(zone, "brightness", str(STATIC_BRIGHTNESS))
        if zone == ZONE_PRIMARY and self._primary_has("enabled"):
            self._write_cached(zone, "enabled", "true")
        self._write_attr(zone, "multi_intensity", self._color_to_sysfs(color))

    def _update_requested_colors(
        self, color: Optional[Color], zone_colors: Optional[dict[str, Color]]
    ) -> None:
        if color is not None and ZONE_PRIMARY in self._available_zones:
            self._requested_colors[ZONE_PRIMARY] = color
        if not zone_colors:
            return
        for zone in (ZONE_SECONDARY, ZONE_REAR):
            if zone in zone_colors and zone in self._available_zones:
                self._requested_colors[zone] = zone_colors[zone]

    def _update_enabled(self, zone_enabled: Optional[dict[str, bool]]) -> None:
        if not zone_enabled:
            return
        for zone in self._available_zones:
            if zone in zone_enabled:
                self._zone_enabled[zone] = bool(zone_enabled[zone])

    def _apply_zone_from_cache(self, zone: str) -> None:
        color = self._requested_colors.get(zone)
        if not self._zone_enabled.get(zone, True):
            self._write_zone_off(zone)
        elif color is not None:
            self._write_static_zone(zone, color)

    def _apply_solid(self) -> None:
        for zone in self._available_zones:
            self._apply_zone_from_cache(zone)

    def _apply_aux(self) -> None:
        for zone in (ZONE_SECONDARY, ZONE_REAR):
            if zone in self._available_zones:
                self._apply_zone_from_cache(zone)

    def _apply_native_preset(
        self,
        mode: RGBMode,
        speed: Optional[str],
        brightness_level: Optional[str],
    ) -> None:
        if ZONE_PRIMARY not in self._available_zones:
            raise RuntimeError("ONEXPLAYER 3 ring LED is unavailable")

        if not self._zone_enabled.get(ZONE_PRIMARY, True):
            self._write_zone_off(ZONE_PRIMARY)
            return

        if mode == RGBMode.OXP_CLASSIC:
            effect = "monocolor"
            color = OXP_CLASSIC_COLOR
        else:
            effect = OXP_EFFECTS[mode]
            color = None

        if effect not in self._effect_tokens():
            raise ValueError(
                f"ONEXPLAYER 3 ring does not expose effect '{effect}'"
            )

        brightness = BRIGHTNESS_LEVELS.get(brightness_level or "high", 100)
        brightness_changed = (
            self._sysfs_cache.get((ZONE_PRIMARY, "brightness")) != str(brightness)
        )
        self._write_cached(ZONE_PRIMARY, "brightness", str(brightness))

        # The PR13 gen3 driver schedules a delayed work item (~50ms) for
        # brightness/RGB writes that resets the effect to monocolor and speed
        # to 5. Writing the effect after that reset has landed keeps the
        # requested preset: wait 100ms for the queued reset to settle and
        # invalidate the cached effect/speed/enabled so they are rewritten.
        # A pure aux-only change (same preset, same brightness) stays fast.
        if brightness_changed or mode != self._current_mode:
            time.sleep(0.1)
            for attr in ("effect", "speed", "enabled"):
                self._sysfs_cache.pop((ZONE_PRIMARY, attr), None)

        self._write_cached(ZONE_PRIMARY, "effect", effect)
        if color is None and self._primary_has("speed"):
            speed_value = SPEED_LEVELS.get(speed or "medium", 5)
            self._write_cached(ZONE_PRIMARY, "speed", str(speed_value))
        if color is not None:
            self._write_attr(
                ZONE_PRIMARY, "multi_intensity", self._color_to_sysfs(color)
            )
        if self._primary_has("enabled"):
            self._write_cached(ZONE_PRIMARY, "enabled", "true")

    def _set_solid_color(self, color: Color) -> None:
        """Software animation callback; only the ring is animated."""
        self._current_color = color
        if ZONE_PRIMARY not in self._available_zones:
            return
        if self._zone_enabled.get(ZONE_PRIMARY, True):
            self._write_static_zone(ZONE_PRIMARY, color)
        else:
            self._write_zone_off(ZONE_PRIMARY)

    def set_color(
        self,
        mode: Optional[RGBMode] = None,
        color: Optional[Color] = None,
        color2: Optional[Color] = None,
        zone_colors: Optional[dict[str, Color]] = None,
        init: bool = False,
        brightness: Optional[int] = None,
        speed: Optional[str] = None,
        brightness_level: Optional[str] = None,
        persist: bool = True,
        **kwargs,
    ):
        """
        Dispatch hardware modes directly so sysfs failures reach the caller.

        The installed BaseLEDDevice lacks supports_software_fallback, so the
        inherited try/catch would silently turn a failed native write into a
        static color. Only software animation modes are delegated to it.
        """
        if init:
            self._sysfs_cache.clear()

        zone_enabled = kwargs.pop("zone_enabled", None)
        if mode is None:
            mode = self._current_mode

        if mode == RGBMode.Disabled:
            self.stop_effects()
            for zone in self._available_zones:
                self._write_zone_off(zone)
            self._current_mode = mode
            self._current_color = Color(0, 0, 0)
            return

        if mode == RGBMode.Solid:
            if color is None:
                return
            self.stop_effects()
            self._update_requested_colors(color, zone_colors)
            self._update_enabled(zone_enabled)
            self._apply_solid()
            self._current_mode = mode
            self._current_color = color
            return

        if mode in OXP_EFFECTS or mode == RGBMode.OXP_CLASSIC:
            if mode not in self.hardware_supported_modes:
                raise ValueError(
                    f"Unsupported ONEXPLAYER 3 hardware mode: {mode}"
                )
            self.stop_effects()
            self._update_requested_colors(color, zone_colors)
            self._update_enabled(zone_enabled)
            self._apply_native_preset(mode, speed, brightness_level)
            self._apply_aux()
            self._current_mode = mode
            if color is not None:
                self._current_color = color
            return

        if mode in SOFTWARE_MODES:
            self._update_requested_colors(color, zone_colors)
            self._update_enabled(zone_enabled)
            super().set_color(
                mode,
                color,
                color2,
                zone_colors=zone_colors,
                init=init,
                brightness=brightness,
                speed=speed,
                brightness_level=brightness_level,
                persist=persist,
                zone_enabled=zone_enabled,
                **kwargs,
            )
            self._apply_aux()
            return

        raise ValueError(f"Unsupported ONEXPLAYER 3 RGB mode: {mode}")

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        capabilities = super().get_mode_capabilities()
        zones = list(self._available_zones)
        for capability in capabilities.values():
            capability.zones = list(zones)

        effects = self._effect_tokens()
        has_speed = self._primary_has("speed")
        for mode, effect in OXP_EFFECTS.items():
            if effect in effects:
                capabilities[mode] = RGBModeCapabilities(
                    mode=mode,
                    color=False,
                    color2=False,
                    speed=has_speed,
                    brightness=False,
                    brightness_level=True,
                    zones=list(zones),
                )
        if "monocolor" in effects:
            capabilities[RGBMode.OXP_CLASSIC] = RGBModeCapabilities(
                mode=RGBMode.OXP_CLASSIC,
                color=False,
                color2=False,
                speed=False,
                brightness=False,
                brightness_level=True,
                zones=list(zones),
            )
        return capabilities

    def get_device_capabilities(self) -> dict:
        zones = []
        for zone in self._available_zones:
            info = {"id": zone, "name_key": ZONE_NAME_KEYS[zone]}
            if zone == ZONE_PRIMARY:
                info["enabled_control"] = True
            zones.append(info)
        return {
            "zones": zones,
            "power_led": False,
            "suspend_mode": False,
            "custom_rgb": False,
        }

    def resume(self, settings: dict = None) -> None:
        """Force static attributes to be rewritten after resume."""
        self._sysfs_cache.clear()
        super().resume(settings)
