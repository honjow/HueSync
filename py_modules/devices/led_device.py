from abc import ABC, abstractmethod
from typing import Optional

from utils import Color, RGBMode, RGBModeCapabilities
from software_effects import PulseEffect, RainbowEffect


class LEDDevice(ABC):
    """Base abstract class for all LED devices"""

    @abstractmethod
    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ):
        pass

    @abstractmethod
    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported mode.
        获取每个支持的模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
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
        self._current_effect: Optional[PulseEffect | RainbowEffect] = None

    @property
    def current_color(self) -> Color | None:
        return self._current_color

    @property
    def current_mode(self) -> RGBMode:
        return self._current_mode

    def _set_solid_color(self, color: Color) -> None:
        """实际设置颜色的方法，子类应该重写此方法"""
        self._current_color = color

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ):
        """
        Default implementation for setting color.
        Subclasses should override this method if they need specific behavior.
        默认的设置颜色实现。如果子类需要特定的行为，应该重写此方法。

        Args:
            mode: RGB mode to set
            color: The primary color to set
            color2: Optional secondary color for modes that support it
        """
        # 停止当前的效果（如果有的话）
        if self._current_effect:
            self._current_effect.stop()
            self._current_effect = None

        if not mode:
            mode = self._current_mode

        if mode == RGBMode.Pulse and color:
            # 创建并启动呼吸灯效果
            self._current_effect = PulseEffect(color, self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Rainbow:
            # 创建并启动彩虹灯效果
            self._current_effect = RainbowEffect(self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Solid and color:
            # 普通的固定颜色模式
            self._set_solid_color(color)

        # 更新当前状态
        if color:
            self._current_color = color
        if mode:
            self._current_mode = mode

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Default mode capabilities.
        默认模式功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        return {
            RGBMode.Disabled: RGBModeCapabilities(
                mode=RGBMode.Disabled,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
        }
