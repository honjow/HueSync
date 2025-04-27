from .led_device import BaseLEDDevice
from config import logger
from led.legion_led_device_hid import LegionGoLEDDeviceHID
from utils import Color, RGBMode, RGBModeCapabilities

GOS_VID = 0x1A86
GOS_XINPUT = 0xE310
GOS_PIDS = {
    GOS_XINPUT: "xinput",
    0xE311: "dinput",
}


class LegionGoLEDDevice(BaseLEDDevice):
    """
    LegionGoLEDDevice provides control for Legion Go LED devices.
    """

    def __init__(self):
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Solid

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [
            RGBMode.Disabled,
            RGBMode.Solid,
            RGBMode.Pulse,
            RGBMode.Rainbow,
            RGBMode.Spiral,
        ]

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
    ) -> None:
        if not color:
            return

        try:
            ledDevice = LegionGoLEDDeviceHID(
                vid=[GOS_VID],
                pid=list(GOS_PIDS),
                usage_page=[0xFFA0],
                usage=[0x0001],
                interface=3,
            )
            if ledDevice.is_ready():
                init = self._current_real_mode != mode or init
                logger.debug(
                    f"set_legion_go_color: mode={mode} color={color} secondary={color2} init={init}"
                )
                if mode:
                    if init:
                        ledDevice.set_led_color(
                            main_color=color,
                            mode=RGBMode.Disabled,
                            close_device=False,
                        )
                    ledDevice.set_led_color(
                        main_color=color,
                        mode=mode,
                        secondary_color=color2,
                        close_device=self.is_current_software_mode(),
                    )
                self._current_real_mode = mode
                return
            logger.info("set_legion_go_color: device not ready")
        except Exception as e:
            logger.error(e, exc_info=True)
            raise

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for devices.
        获取设备每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping RGB modes to their capabilities.
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
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                color=False,
                color2=False,
                speed=True,
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                color=True,
                color2=False,
                speed=True,
            ),
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                color=False,
                color2=False,
                speed=True,
            ),
            RGBMode.Duality: RGBModeCapabilities(
                mode=RGBMode.Duality,
                color=True,
                color2=True,
                speed=True,
            ),
            RGBMode.Battery: RGBModeCapabilities(
                mode=RGBMode.Battery,
                color=False,
                color2=False,
                speed=False,
                brightness=True,
            ),
        }
