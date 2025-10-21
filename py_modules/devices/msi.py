from config import logger
from led.msi_led_device_hid import MSILEDDeviceHID
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice

MSI_CLAW_VID = 0x0DB0
MSI_CLAW_XINPUT_PID = 0x1901
MSI_CLAW_DINPUT_PID = 0x1902

KBD_VID = 0x0001
KBD_PID = 0x0001


class MSILEDDevice(BaseLEDDevice):
    """
    MSILEDDevice provides control for MSI LED devices.
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
            RGBMode.Duality,
            RGBMode.Gradient,
            RGBMode.MSI_FROSTFIRE,
            RGBMode.OXP_SUN,
        ]

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    def _convert_speed_to_int(self, speed: str) -> int:
        """
        Convert speed string to integer value for MSI protocol.
        将速度字符串转换为 MSI 协议的整数值。
        
        Args:
            speed: "low", "medium", or "high"
            
        Returns:
            int: Speed value (0-20, higher = faster)
        """
        speed_map = {
            "low": 6,      # Slow speed
            "medium": 10,  # Medium speed
            "high": 17,    # Fast speed
        }
        return speed_map.get(speed, 10)  # Default to medium

    def _convert_brightness_to_int(self, brightness_level: str) -> int:
        """
        Convert brightness level string to integer value.
        将亮度级别字符串转换为整数值。
        
        Args:
            brightness_level: "low", "medium", or "high"
            
        Returns:
            int: Brightness value (0-100)
        """
        brightness_map = {
            "low": 33,      # ~33% brightness
            "medium": 66,   # ~66% brightness
            "high": 100,    # 100% brightness
        }
        return brightness_map.get(brightness_level, 100)  # Default to high

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
        brightness_level: str | None = None,
        **kwargs,  # Accept other future parameters
    ) -> None:
        if not color:
            return

        # Convert string speed to integer (0-20, higher = faster)
        # 将字符串速度转换为整数（0-20，越大越快）
        speed_value = self._convert_speed_to_int(speed) if speed else 15
        
        # Convert string brightness_level to integer (0-100)
        # 将字符串亮度级别转换为整数（0-100）
        brightness_value = self._convert_brightness_to_int(brightness_level) if brightness_level else 100

        try:
            ledDevice = MSILEDDeviceHID(
                vid=[MSI_CLAW_VID],
                pid=[MSI_CLAW_XINPUT_PID, MSI_CLAW_DINPUT_PID],
                usage_page=[0xFFA0, 0xFFF0],
                usage=[0x0001, 0x0040],
            )
            if ledDevice.is_ready():
                init = self._current_real_mode != mode or init
                logger.debug(
                    f"set_msi_color: mode={mode} color={color} secondary={color2} "
                    f"speed={speed}({speed_value}) brightness_level={brightness_level}({brightness_value}) init={init}"
                )
                if mode:
                    if init:
                        ledDevice.set_led_color(main_color=color, mode=RGBMode.Disabled)
                    ledDevice.set_led_color(
                        main_color=color,
                        mode=mode,
                        secondary_color=color2,
                        brightness=brightness_value,
                        speed=speed_value,
                    )
                self._current_real_mode = mode or RGBMode.Disabled
                return
            logger.info("set_msi_color: device not ready")
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
                brightness=False,
                brightness_level=False,
            ),
            RGBMode.Solid: RGBModeCapabilities(
                mode=RGBMode.Solid,
                color=True,
                color2=False,
                speed=False,
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.Rainbow: RGBModeCapabilities(
                mode=RGBMode.Rainbow,
                color=False,
                color2=False,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.Pulse: RGBModeCapabilities(
                mode=RGBMode.Pulse,
                color=True,
                color2=False,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                color=False,
                color2=False,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.Duality: RGBModeCapabilities(
                mode=RGBMode.Duality,
                color=True,
                color2=True,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.Gradient: RGBModeCapabilities(
                mode=RGBMode.Gradient,
                color=True,
                color2=True,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.MSI_FROSTFIRE: RGBModeCapabilities(
                mode=RGBMode.MSI_FROSTFIRE,
                color=False,
                color2=False,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.OXP_SUN: RGBModeCapabilities(
                mode=RGBMode.OXP_SUN,
                color=False,
                color2=False,
                speed=True,  # Hardware speed support
                brightness=False,
                brightness_level=True,  # Hardware brightness support
            ),
            RGBMode.Battery: RGBModeCapabilities(
                mode=RGBMode.Battery,
                color=False,
                color2=False,
                speed=False,
                brightness=True,  # Battery mode uses HSV brightness
                brightness_level=False,
            ),
        }
