from config import logger
from led.legion_go_tablet_hid import LegionGoTabletHID
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice
from .legion_power_led_mixin import LegionPowerLEDMixin


class LegionGoTabletLEDDevice(LegionPowerLEDMixin, BaseLEDDevice):
    """
    LegionGoTabletLEDDevice provides RGB control for Legion Go tablet mode controllers.
    Supports left and right detachable controllers with synchronized RGB control.
    Includes controller RGB control (via HID) and power LED control (via EC).
    
    为Legion Go平板模式控制器提供RGB控制。
    支持左右可拆卸控制器的同步RGB控制。
    
    Supported models:
    - Legion Go (83E1) - PID: 0x6182-0x6185 (xinput/dinput/dual_dinput/fps modes)
    - Legion Go 2/1 with 2025 Firmware (83N0, 83N1) - PID: 0x61EB-0x61EE
    - Legion Go S (83L3, 83N6, 83Q2, 83Q3) - Uses different EC register for power LED
    
    Note: This is for Legion Go tablet mode, including Legion Go S.
    注意：这适用于 Legion Go 平板模式，包括 Legion Go S。
    
    Device modes (by PID):
    - 0x6182/0x61EB: xinput mode (default)
    - 0x6183/0x61EC: dinput mode
    - 0x6184/0x61ED: dual_dinput mode
    - 0x6185/0x61EE: fps mode
    """
    
    # Power LED configuration for Legion Go S
    # EC register offset and bit position for power LED control
    # Reference: DSDT analysis from hwinfo/devices/legion_go_s/acpi/QCCN17WW
    # Note: Legion Go S uses different register than original Legion Go
    POWER_LED_OFFSET = 0x10  # LPBL field in EC memory
    POWER_LED_BIT = 6        # Bit 6 controls power LED

    def __init__(self):
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Disabled
        self._profile = 3  # Use profile 3 for all settings

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        """
        List of RGB modes supported by Legion Go hardware.
        Legion Go硬件支持的RGB模式列表。
        
        Returns:
            list[RGBMode]: Supported modes
        """
        return [
            RGBMode.Disabled,
            RGBMode.Solid,
            RGBMode.Pulse,
            RGBMode.Rainbow,
            RGBMode.Spiral,
        ]

    def _set_solid_color(self, color: Color) -> None:
        """
        Set solid color (called by software effects).
        设置纯色（由软件效果调用）。
        """
        self._set_hardware_color(RGBMode.Solid, color)

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
        **kwargs,  # Accept brightness_level and other future parameters
    ) -> None:
        """
        Set hardware RGB color and mode on Legion Go controllers.
        在Legion Go控制器上设置硬件RGB颜色和模式。
        
        This method handles communication with the Legion Go receiver device
        and synchronizes settings across both left and right controllers.
        此方法处理与Legion Go接收器设备的通信，并在左右控制器之间同步设置。
        
        Args:
            mode: RGB mode to set
            color: Primary color (RGB values)
            color2: Secondary color (not used for Legion Go)
            init: Whether this is an initialization call
            speed: Animation speed ("low", "medium", "high")
        """
        if not color:
            return

        try:
            # Legion Go uses a receiver device for wireless communication
            # Based on HHD reverse engineering - confirmed parameters
            ledDevice = LegionGoTabletHID(
                vid=[0x17EF],  # Lenovo VID
                # Support all controller modes and firmware versions
                pid=[
                    0x6182,  # xinput mode (Legion Go 1)
                    0x6183,  # dinput mode
                    0x6184,  # dual_dinput mode
                    0x6185,  # fps mode
                    0x61EB,  # xinput mode (Legion Go 2/1 with 2025 Firmware)
                    0x61EC,  # dinput mode (2025 Firmware)
                    0x61ED,  # dual_dinput mode (2025 Firmware)
                    0x61EE,  # fps mode (2025 Firmware)
                ],
                usage_page=[0xFFA0],  # Confirmed: 0xFFA0 (not 0xFF00)
                usage=[0x0001],
            )
            
            if ledDevice.is_ready():
                init = self._current_real_mode != mode or init
                logger.debug(
                    f"set_legion_go_tablet_color: mode={mode} color={color} "
                    f"secondary={color2} init={init} speed={speed}"
                )
                
                if mode:
                    brightness = 100  # Default brightness (will be converted to 0-1)
                    ledDevice.set_led_color(
                        mode=mode,
                        color=color,
                        brightness=brightness,
                        speed=speed or "medium",
                        init=init,
                    )
                    
                self._current_real_mode = mode or RGBMode.Disabled
                return
                
            logger.info("set_legion_go_tablet_color: device not ready")
        except Exception as e:
            logger.error(e, exc_info=True)
            raise

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for Legion Go Tablet.
        获取 Legion Go 平板模式每个支持的 RGB 模式的功能支持情况。

        Legion Go supports:
        - Solid: color control
        - Pulse: color + speed control
        - Rainbow (dynamic): brightness + speed control
        - Spiral: brightness + speed control
        
        Note: Duality mode is not supported by Legion Go hardware,
        it will be handled by software effects in BaseLEDDevice.
        注意：Legion Go硬件不支持Duality模式，
        它将由BaseLEDDevice中的软件效果处理。

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
                brightness=True,
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
                brightness=True,
            ),
            RGBMode.Duality: RGBModeCapabilities(
                mode=RGBMode.Duality,
                color=True,
                color2=True,
                speed=True,
            ),
            RGBMode.Gradient: RGBModeCapabilities(
                mode=RGBMode.Gradient,
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

