from config import logger
from led.zotac_led_device_hid import (
    ZotacLEDDeviceHID,
    BRIGHTNESS_LOW,
    BRIGHTNESS_MED,
    BRIGHTNESS_MAX,
    EFFECT_BREATHE,
    EFFECT_FADE,
    EFFECT_FLASH,
    EFFECT_RAINBOW,
    EFFECT_RANDOM,
    EFFECT_SOLID,
    EFFECT_STARS,
    EFFECT_WINK,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,

)
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


def _brightness_value(brightness_level: str = None) -> int:
    """Map HueSync brightness levels to Zotac firmware brightness values."""
    mapping = {
        "low": BRIGHTNESS_LOW,
        "medium": BRIGHTNESS_MED,
        "high": BRIGHTNESS_MAX,
    }
    return mapping.get(brightness_level or "high", BRIGHTNESS_MAX)


def _speed_value(speed: str = None) -> int:
    """Map HueSync speed levels to Zotac firmware speed values."""
    mapping = {
        "low": SPEED_LOW,
        "medium": SPEED_MEDIUM,
        "high": SPEED_HIGH,
    }
    return mapping.get(speed or "medium", SPEED_MEDIUM)


class ZotacLEDDevice(BaseLEDDevice):
    """HueSync-facing Zotac backend for the currently confirmed hardware modes."""

    def __init__(self):
        super().__init__()
        # Cache the opened HID transport so repeated writes reuse the same device handle.
        self._hid_device = None

    @classmethod
    def should_use(cls) -> bool:
        try:
            return ZotacLEDDeviceHID.has_supported_device()
        except Exception as error:
            logger.warning(f"Failed to probe Zotac HID devices: {error}")
            return False

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [
            RGBMode.Solid,
            RGBMode.Rainbow,
            RGBMode.Spiral,
            RGBMode.Pulse,
            RGBMode.ZOTAC_STARS,
            RGBMode.ZOTAC_FLASH,
            RGBMode.ZOTAC_WINK,
            RGBMode.ZOTAC_RANDOM,
            RGBMode.Disabled,
        ]

    def _get_device(self):
        """Get a cached Zotac HID device or open it lazily on first use."""
        if self._hid_device and self._hid_device.is_ready():
            return self._hid_device

        self._hid_device = ZotacLEDDeviceHID()
        if self._hid_device.is_ready():
            return self._hid_device

        self._hid_device = None
        return None

    def _set_hardware_color(
        self,
        mode: RGBMode = None,
        color: Color = None,
        color2: Color = None,
        init: bool = False,
        speed: str = None,
        brightness_level: str = None,
        **kwargs,
    ) -> None:
        if not color:
            return

        device = self._get_device()
        if not device:
            logger.warning("Zotac command interface is not available")
            return

        brightness = _brightness_value(brightness_level)
        speed = _speed_value(speed)

        try:
            if mode == RGBMode.Disabled:
                device.apply_disabled()
            elif mode == RGBMode.Solid:
                device.apply_effect(EFFECT_SOLID, color, speed, brightness)
            elif mode == RGBMode.Pulse:
                device.apply_effect(EFFECT_BREATHE, color, speed, brightness)
            elif mode == RGBMode.Rainbow:
                device.apply_effect(EFFECT_FADE, color, speed, brightness)
            elif mode == RGBMode.Spiral:
                device.apply_effect(EFFECT_RAINBOW, color, speed, brightness)
            elif mode == RGBMode.ZOTAC_STARS:
                device.apply_effect(EFFECT_STARS, color, speed, brightness)
            elif mode == RGBMode.ZOTAC_FLASH:
                device.apply_effect(EFFECT_FLASH, color, speed, brightness)
            elif mode == RGBMode.ZOTAC_WINK:
                device.apply_effect(EFFECT_WINK, color, speed, brightness)
            elif mode == RGBMode.ZOTAC_RANDOM:
                device.apply_effect(EFFECT_RANDOM, color, speed, brightness)
            else:
                raise ValueError(f"Unsupported Zotac RGB mode: {mode}")
        except Exception as error:
            logger.error(f"Failed to set Zotac RGB mode {mode}: {error}", exc_info=True)
            self._hid_device = None
            raise

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """Describe the Zotac modes and controls currently exposed to HueSync."""
        return {
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                color=True,
                color2=False,
                speed=False,
                brightness_level=True,
            ),
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                color=False,
                color2=False,
                speed=True,
                brightness_level=True,
            ),
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                color=False,
                color2=False,
                speed=True,
                brightness_level=True,
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                color=True,
                color2=False,
                speed=True,
                brightness_level=True,
            ),
            RGBMode.ZOTAC_STARS: RGBModeCapabilities(
                mode=RGBMode.ZOTAC_STARS,
                color=True,
                color2=False,
                speed=True,
                brightness_level=True,
            ),
            RGBMode.ZOTAC_FLASH: RGBModeCapabilities(
                mode=RGBMode.ZOTAC_FLASH,
                color=False,
                color2=False,
                speed=True,
                brightness_level=False,
            ),
            RGBMode.ZOTAC_WINK: RGBModeCapabilities(
                mode=RGBMode.ZOTAC_WINK,
                color=True,
                color2=False,
                speed=True,
                brightness_level=True,
            ),
            RGBMode.ZOTAC_RANDOM: RGBModeCapabilities(
                mode=RGBMode.ZOTAC_RANDOM,
                color=True,
                color2=False,
                speed=True,
                brightness_level=True,
            ),
            RGBMode.Disabled: RGBModeCapabilities(
                mode=RGBMode.Disabled,
                color=False,
                color2=False,
                speed=False,
                brightness_level=False,
            ),
        }

    def get_device_capabilities(self) -> dict:
        """Return Zotac device capabilities using the default single-zone HueSync shape."""
        caps = super().get_device_capabilities()
        caps["suspend_mode"] = False
        return caps

    def suspend(self, settings: dict = None) -> None:
        if self._hid_device:
            self._hid_device.close()
        self._hid_device = None

    def resume(self, settings: dict = None) -> None:
        if self._hid_device:
            self._hid_device.close()
        self._hid_device = None
