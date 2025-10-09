from abc import ABC, abstractmethod
from typing import Optional

from config import logger
from software_effects import BatteryEffect, DualityEffect, GradientEffect, PulseEffect, RainbowEffect
from utils import Color, RGBMode, RGBModeCapabilities


class LEDDevice(ABC):
    """Base abstract class for all LED devices"""

    @abstractmethod
    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
        brightness_level: str | None = None,
        **kwargs,  # Accept any additional parameters for future extension
    ):
        """
        Set LED color and mode.
        
        Args:
            mode: RGB mode to set
            color: Primary color
            color2: Secondary color (for dual-color modes)
            init: Whether this is an initialization call
            brightness: Software brightness (0-100, for HSV-based modes)
            speed: Animation speed ("low", "medium", "high")
            brightness_level: Hardware brightness level ("low", "medium", "high")
            **kwargs: Additional parameters for future extension
        """
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

    @abstractmethod
    def get_suspend_mode(self) -> str:
        pass

    @abstractmethod
    def set_suspend_mode(self, mode: str) -> None:
        pass

    @abstractmethod
    def suspend(self) -> None:
        pass

    @abstractmethod
    def resume(self) -> None:
        pass


class BaseLEDDevice(LEDDevice):
    """
    Base implementation of LEDDevice with common functionality.
    Provides default implementations that can be overridden by specific device classes.
    """

    def __init__(self):
        self._current_color: Color | None = None
        self._current_mode: RGBMode = RGBMode.Solid
        self._current_effect: Optional[
            PulseEffect | RainbowEffect | DualityEffect | GradientEffect | BatteryEffect
        ] = None

    @property
    def current_color(self) -> Color | None:
        return self._current_color

    @property
    def current_mode(self) -> RGBMode:
        return self._current_mode

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        """
        Subclasses should override this method to return list of supported hardware lighting modes
        子类应该重写此方法，返回支持的硬件灯效模式列表
        """
        return []

    def is_current_software_mode(self) -> bool:
        return self._current_mode not in self.hardware_supported_modes

    def _set_solid_color(self, color: Color) -> None:
        """
        Actual color setting method, subclasses should override this method
        实际设置颜色的方法，子类应该重写此方法
        """
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
        speed: str | None = None,
        brightness_level: str | None = None,
        **kwargs,  # Accept any additional parameters for future extension
    ) -> None:
        """
        Subclasses should override this method to implement hardware lighting control
        子类应该重写此方法，实现硬件灯效控制
        
        Args:
            mode: RGB mode to set
            color: Primary color
            color2: Secondary color (for dual-color modes)
            init: Whether this is an initialization call
            speed: Animation speed ("low", "medium", "high")
            brightness_level: Hardware brightness level ("low", "medium", "high")
            **kwargs: Additional parameters for future extension
        """
        raise NotImplementedError

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
        brightness_level: str | None = None,
        **kwargs,  # Accept any additional parameters for future extension
    ):
        """
        Default implementation for setting color.
        Subclasses should override hardware_supported_modes and _set_hardware_color.
        
        Args:
            mode: RGB mode to set
            color: Primary color
            color2: Secondary color (for dual-color modes)
            init: Whether this is an initialization call
            brightness: Software brightness (0-100, for HSV-based modes)
            speed: Animation speed ("low", "medium", "high")
            brightness_level: Hardware brightness level ("low", "medium", "high")
            **kwargs: Additional parameters for future extension
        """
        if not color:
            return

        if not mode:
            mode = self._current_mode

        # If hardware-supported LED mode, try hardware implementation | 如果是支持硬件的灯效模式，尝试使用硬件实现
        if mode in self.hardware_supported_modes:
            try:
                logger.info(f"use hardware control: mode={mode}")
                self.stop_effects()
                self._set_hardware_color(mode, color, color2, init, speed=speed, brightness_level=brightness_level, **kwargs)
                return
            except Exception as e:
                logger.error(e, exc_info=True)
                # If hardware control fails, fallback to software implementation | 如果硬件控制失败，回退到软件实现
                pass

        logger.info(f"use software control: mode={mode}")
        # Stop current effect (if any) | 停止当前的效果（如果有的话）
        self.stop_effects()

        # Use software implementation | 使用软件实现
        if mode == RGBMode.Pulse and color:
            # Create and start breathing effect | 创建并启动呼吸灯效果
            self._current_effect = PulseEffect(color, self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Rainbow:
            # Create and start rainbow effect | 创建并启动彩虹灯效果
            self._current_effect = RainbowEffect(self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Duality and color and color2:
            # Create and start dual-color alternating pulse effect | 创建并启动双色交替呼吸效果
            self._current_effect = DualityEffect(color, color2, self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Gradient and color and color2:
            # Create and start dual-color gradient transition effect | 创建并启动双色渐变过渡效果
            self._current_effect = GradientEffect(color, color2, self._set_solid_color)
            self._current_effect.start()
        elif mode == RGBMode.Battery:
            # Create and start battery status effect | 创建并启动电池状态灯效果
            self._current_effect = BatteryEffect(
                self._set_solid_color,
                base_brightness=brightness if brightness else 100,
            )
            self._current_effect.start()
        elif mode == RGBMode.Solid:
            # Directly set color | 直接设置颜色
            self._set_solid_color(color)
        elif mode == RGBMode.Disabled:
            # Set to disabled state | 设置为禁用状态
            self._set_solid_color(Color(0, 0, 0))
        else:
            # Other modes directly set color | 其他模式直接设置颜色
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

    def get_suspend_mode(self) -> str:
        return ""

    def set_suspend_mode(self, mode: str) -> None:
        return

    def suspend(self) -> None:
        return

    def resume(self) -> None:
        return
