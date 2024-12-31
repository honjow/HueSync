from abc import ABC, abstractmethod

from utils import Color, RGBMode, RGBModeCapabilities


class LEDDevice(ABC):
    """Base abstract class for all LED devices"""

    @abstractmethod
    def set_color(
        self,
        mode: str | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ):
        pass

    @abstractmethod
    def get_supported_modes(self) -> list[RGBMode]:
        pass

    @abstractmethod
    def get_mode_capabilities(self) -> dict[str, RGBModeCapabilities]:
        """
        Get the capabilities of each supported mode.
        获取每个支持的模式的功能支持情况。

        Returns:
            dict[str, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
            dict[str, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        pass


class BaseLEDDevice(LEDDevice):
    """
    Base implementation of LEDDevice with common functionality.
    Provides default implementations that can be overridden by specific device classes.
    """

    def __init__(self):
        self._current_color: Color | None = None
        self._current_mode: RGBMode = RGBMode.Solid

    @property
    def current_color(self) -> Color | None:
        return self._current_color

    @property
    def current_mode(self) -> str:
        return self._current_mode.value

    def set_color(
        self,
        mode: str | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ):
        """
        Default implementation for setting color.
        Subclasses should override this method if they need specific behavior.

        Args:
            mode: RGB mode to set
            color: The primary color to set
            color2: Optional secondary color for modes that support it
        """
        if color:
            self._current_color = color
        if mode:
            try:
                rgb_mode = next((m for m in RGBMode if m.value == mode.lower()), None)
                if rgb_mode:
                    self._current_mode = rgb_mode
            except Exception:
                pass  # Invalid mode name

    def get_supported_modes(self) -> list[RGBMode]:
        """
        Default supported modes.
        Subclasses should override this to provide their specific supported modes.
        """
        return [RGBMode.Disabled, RGBMode.Solid]

    def get_mode_capabilities(self) -> dict[str, RGBModeCapabilities]:
        """
        Default mode capabilities.
        默认模式功能支持情况。

        Returns:
            dict[str, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
            dict[str, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        return {
            RGBMode.Disabled.value: RGBModeCapabilities(
                mode=RGBMode.Disabled,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Solid.value: RGBModeCapabilities(
                mode=RGBMode.Solid,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Rainbow.value: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                supports_color=False,
                supports_color2=False,
                supports_speed=True,
            ),
            RGBMode.Pulse.value: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                supports_color=True,
                supports_color2=False,
                supports_speed=True,
            ),
        }
