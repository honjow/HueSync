import time

from config import PRODUCT_NAME, SYS_VENDOR, logger
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


ZOTAC_APPLY_ATTEMPTS = 4
ZOTAC_RETRY_DELAY_SECONDS = 0.5


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
        if SYS_VENDOR == "ZOTAC" and PRODUCT_NAME == "ZOTAC GAMING ZONE":
            return True
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

    @property
    def supports_software_fallback(self) -> bool:
        # Zotac has no software transport behind _set_solid_color. Treating a
        # failed HID transaction as a software success prevents later retries.
        return False

    def _discard_device(self) -> None:
        device = self._hid_device
        self._hid_device = None
        if not device:
            return

        try:
            device.close()
        except Exception as error:
            logger.debug(f"Failed to close Zotac command interface: {error}")

    def _get_device(self):
        """Get a cached Zotac HID device or open it lazily on first use."""
        if self._hid_device and self._hid_device.is_ready():
            return self._hid_device

        self._discard_device()
        self._hid_device = ZotacLEDDeviceHID()
        if self._hid_device.is_ready():
            return self._hid_device

        self._discard_device()
        return None

    @staticmethod
    def _apply_to_device(
        device: ZotacLEDDeviceHID,
        mode: RGBMode,
        color: Color,
        speed: int,
        brightness: int,
        persist: bool,
    ) -> None:
        if mode == RGBMode.Disabled:
            device.apply_disabled(persist=persist)
        elif mode == RGBMode.Solid:
            device.apply_effect(
                EFFECT_SOLID, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.Pulse:
            device.apply_effect(
                EFFECT_BREATHE, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.Rainbow:
            device.apply_effect(
                EFFECT_FADE, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.Spiral:
            device.apply_effect(
                EFFECT_RAINBOW, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.ZOTAC_STARS:
            device.apply_effect(
                EFFECT_STARS, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.ZOTAC_FLASH:
            device.apply_effect(
                EFFECT_FLASH, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.ZOTAC_WINK:
            device.apply_effect(
                EFFECT_WINK, color, speed, brightness, persist=persist
            )
        elif mode == RGBMode.ZOTAC_RANDOM:
            device.apply_effect(
                EFFECT_RANDOM, color, speed, brightness, persist=persist
            )
        else:
            raise ValueError(f"Unsupported Zotac RGB mode: {mode}")

    def _set_hardware_color(
        self,
        mode: RGBMode = None,
        color: Color = None,
        color2: Color = None,
        init: bool = False,
        speed: str = None,
        brightness_level: str = None,
        persist: bool = True,
        **kwargs,
    ) -> None:
        if not color:
            return

        brightness = _brightness_value(brightness_level)
        speed = _speed_value(speed)
        last_error = None
        retry_delay = ZOTAC_RETRY_DELAY_SECONDS

        for attempt in range(1, ZOTAC_APPLY_ATTEMPTS + 1):
            if attempt > 1:
                logger.info(
                    f"Retrying Zotac RGB transaction "
                    f"({attempt}/{ZOTAC_APPLY_ATTEMPTS})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2

            try:
                device = self._get_device()
                if not device:
                    raise RuntimeError("Zotac command interface is not available")

                self._apply_to_device(
                    device,
                    mode,
                    color,
                    speed,
                    brightness,
                    persist,
                )
                return
            except Exception as error:
                last_error = error
                logger.warning(
                    f"Zotac RGB transaction attempt {attempt} failed: {error}"
                )
                self._discard_device()

        raise RuntimeError(
            f"Failed to set Zotac RGB mode {mode} after "
            f"{ZOTAC_APPLY_ATTEMPTS} attempts"
        ) from last_error

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
        self._discard_device()

    def resume(self, settings: dict = None) -> None:
        self._discard_device()
