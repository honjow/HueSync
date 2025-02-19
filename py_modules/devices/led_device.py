from abc import ABC, abstractmethod
from typing import Optional

from utils import Color, RGBMode, RGBModeCapabilities
from software_effects import PulseEffect, RainbowEffect, DualityEffect, BatteryEffect
from config import logger


class LEDDevice(ABC):
    """Base abstract class for all LED devices"""

    @abstractmethod
    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: float | None = None,
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
        self._current_effect: Optional[PulseEffect | RainbowEffect | DualityEffect] = (
            None
        )

    @property
    def current_color(self) -> Color | None:
        return self._current_color

    @property
    def current_mode(self) -> RGBMode:
        return self._current_mode

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        """子类应该重写此方法，返回支持的硬件灯效模式列表"""
        return []

    def _set_solid_color(self, color: Color) -> None:
        """实际设置颜色的方法，子类应该重写此方法"""
        self._current_color = color

    def stop_effects(self):
        if self._current_effect:
            self._current_effect.stop()
            self._current_effect = None

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
    ) -> None:
        """子类应该重写此方法，实现硬件灯效控制"""
        raise NotImplementedError

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: int | None = None,
    ):
        """
        Default implementation for setting color.
        Subclasses should override hardware_supported_modes and _set_hardware_color.
        """
        if not color:
            return

        if not mode:
            mode = self._current_mode

        # 如果是支持硬件的灯效模式，尝试使用硬件实现
        if mode in self.hardware_supported_modes:
            try:
                logger.info(f"use hardware control: mode={mode}")
                self.stop_effects()
                self._set_hardware_color(mode, color, color2, init)
                return
            except Exception as e:
                logger.error(e, exc_info=True)
                # 如果硬件控制失败，回退到软件实现
                pass

        logger.info(f"use software control: mode={mode}")
        # 停止当前的效果（如果有的话）
        self.stop_effects()

        # 使用软件实现
        if mode == RGBMode.Pulse and color:
            # 创建并启动呼吸灯效果
            self._current_effect = PulseEffect(color, self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Rainbow:
            # 创建并启动彩虹灯效果
            self._current_effect = RainbowEffect(self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Duality and color and color2:
            # 创建并启动双色过渡效果
            self._current_effect = DualityEffect(color, color2, self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Battery:
            # 创建并启动电池状态灯效果
            self._current_effect = BatteryEffect(
                self._set_solid_color, base_brightness=brightness
            )
            self._current_effect.start()
        elif mode == RGBMode.Solid:
            # 直接设置颜色
            self._set_solid_color(color)
        elif mode == RGBMode.Disabled:
            # 设置为禁用状态
            self._set_solid_color(Color(0, 0, 0))
        else:
            # 其他模式直接设置颜色
            self._set_solid_color(color)

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
                color=False,
                color2=False,
                speed=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                color=True,
                color2=False,
                speed=False,
            ),
        }
