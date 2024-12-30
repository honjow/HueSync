from abc import ABC, abstractmethod

from utils import Color, RGBMode


class LEDDevice(ABC):
    """Base abstract class for all LED devices"""

    @abstractmethod
    def set_color(self, color: Color, brightness: int):
        pass

    @abstractmethod
    def set_mode(self, mode: str):
        pass

    @abstractmethod
    def get_supported_modes(self) -> list[RGBMode]:
        pass


class BaseLEDDevice(LEDDevice):
    """
    Base implementation of LEDDevice with common functionality.
    Provides default implementations that can be overridden by specific device classes.
    """

    def __init__(self):
        self._current_color: Color | None = None
        self._current_brightness: int = 100
        self._current_mode: RGBMode = RGBMode.Solid

    @property
    def current_color(self) -> Color | None:
        return self._current_color

    @property
    def current_brightness(self) -> int:
        return self._current_brightness

    @property
    def current_mode(self) -> RGBMode:
        return self._current_mode

    def set_color(self, color: Color, brightness: int):
        """
        Default implementation for setting color and brightness.
        Subclasses should override this method if they need specific behavior.
        """
        self._current_color = color
        self._current_brightness = max(
            0, min(100, brightness)
        )  # Ensure brightness is between 0-100

    def set_mode(self, mode: str):
        """
        Default implementation for setting mode.
        Subclasses should override this method if they need specific behavior.
        """
        try:
            # 尝试直接从字符串获取模式
            rgb_mode = next(
                (m for m in RGBMode if m.value == mode.lower()),
                None
            )
            if rgb_mode and rgb_mode in self.get_supported_modes():
                self._current_mode = rgb_mode
        except Exception:
            pass  # Invalid mode name

    def get_supported_modes(self) -> list[RGBMode]:
        """
        Default supported modes.
        Subclasses should override this to provide their specific supported modes.
        """
        return [RGBMode.Disabled, RGBMode.Solid]
