from abc import ABC, abstractmethod

from utils import Color, RGBMode


class LEDDevice(ABC):
    """Base abstract class for all LED devices"""

    @abstractmethod
    def set_color(
        self,
        mode: str | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        brightness: int = 100,
    ):
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
    def current_mode(self) -> str:
        return self._current_mode.value

    def set_color(
        self,
        mode: str | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        brightness: int = 100,
    ):
        """
        Default implementation for setting color and brightness.
        Subclasses should override this method if they need specific behavior.

        Args:
            mode: RGB mode to set
            color: The primary color to set
            color2: Optional secondary color for modes that support it
            brightness: The brightness level (0-100)
        """
        if color:
            self._current_color = color
        if mode:
            try:
                rgb_mode = next((m for m in RGBMode if m.value == mode.lower()), None)
                if rgb_mode and rgb_mode in self.get_supported_modes():
                    self._current_mode = rgb_mode
            except Exception:
                pass  # Invalid mode name
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
            rgb_mode = next((m for m in RGBMode if m.value == mode.lower()), None)
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
