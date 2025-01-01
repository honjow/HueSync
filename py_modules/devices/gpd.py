from config import (
    DEFAULT_BRIGHTNESS,
    logger,
)

from utils import Color, RGBMode, RGBModeCapabilities
from wincontrols.hardware import WinControls
from .led_device import BaseLEDDevice


class GPDLEDDevice(BaseLEDDevice):
    """
    GPDLEDDevice is tailored for GPD devices, allowing specific control over
    color and mode settings.

    GPDLEDDevice专为GPD设备设计，允许对颜色和模式设置进行特定控制。
    """

    def __init__(self):
        super().__init__()
        self._use_software_effects = False

    def _set_solid_color(self, color: Color) -> None:
        """实际设置颜色的方法"""
        try:
            wc = WinControls(disableFwCheck=True)
            _color = Color(
                color.R * DEFAULT_BRIGHTNESS // 100,
                color.G * DEFAULT_BRIGHTNESS // 100,
                color.B * DEFAULT_BRIGHTNESS // 100,
            )
            conf = ["ledmode=solid", f"colour={_color.hex()}"]
            logger.info(f"conf={conf}")
            if wc.setConfig(config=conf):
                wc.writeConfig()
        except Exception as e:
            logger.error(e, exc_info=True)

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
    ) -> None:
        if not color:
            return

        # 如果是软件效果，使用父类实现
        if self._use_software_effects or mode in [RGBMode.Rainbow]:
            self._use_software_effects = True
            super().set_color(mode, color, color2)
            return

        try:
            wc = WinControls(disableFwCheck=True)
            _color = Color(
                color.R * DEFAULT_BRIGHTNESS // 100,
                color.G * DEFAULT_BRIGHTNESS // 100,
                color.B * DEFAULT_BRIGHTNESS // 100,
            )
            ledmode = "solid"
            match mode:
                case RGBMode.Solid:
                    ledmode = "solid"
                    self._use_software_effects = False
                case RGBMode.Disabled:
                    ledmode = "off"
                    self._use_software_effects = False
                case RGBMode.Pulse:
                    ledmode = "breathe"
                    self._use_software_effects = False
                case RGBMode.Spiral:
                    ledmode = "rotate"
                    self._use_software_effects = False
                case _:
                    # 对于不支持的模式，使用软件实现
                    self._use_software_effects = True
                    super().set_color(mode, color, color2)
                    return

            conf = [f"ledmode={ledmode}", f"colour={_color.hex()}"]
            logger.info(f"conf={conf}")
            if wc.setConfig(config=conf):
                wc.writeConfig()

        except Exception as e:
            logger.error(e, exc_info=True)
            # 如果硬件控制失败，尝试使用软件实现
            self._use_software_effects = True
            super().set_color(mode, color, color2)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        获取每个支持的模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
        """
        capabilities = {
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
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                supports_color=True,
                supports_color2=False,
                supports_speed=False,
            ),
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                supports_color=False,
                supports_color2=False,
                supports_speed=False,
            ),
            # 添加软件支持的模式
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                supports_color=False,
                supports_color2=False,
                supports_speed=True,
            ),
        }
        return capabilities
