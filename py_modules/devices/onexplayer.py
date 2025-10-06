import time

from config import PRODUCT_NAME, logger
from led.onex_led_device_hid import (
    X1_MINI_PAGE,
    X1_MINI_PID,
    X1_MINI_USAGE,
    X1_MINI_VID,
    XFLY_PAGE,
    XFLY_PID,
    XFLY_USAGE,
    XFLY_VID,
    OneXLEDDeviceHID,
)
from led.onex_led_device_serial import OneXLEDDeviceSerial
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice
from .onexplayer_configs import OXPProtocol, get_config


class OneXLEDDevice(BaseLEDDevice):
    """
    OneXLEDDevice is designed for OneX devices, enabling HID and serial communication
    for color and mode settings.

    OneXLEDDevice专为OneX设备设计，支持HID和串行通信以进行颜色和模式设置。
    """

    def __init__(self):
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Solid
        
        # Get device configuration
        # 获取设备配置
        self._config = get_config(PRODUCT_NAME)
        if self._config:
            logger.info(
                f"OneXPlayer config: name={self._config.name}, "
                f"protocol={self._config.protocol.value}, rgb={self._config.rgb}"
            )
        else:
            logger.warning(f"Unknown OneXPlayer model: {PRODUCT_NAME}")

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        """
        List of RGB modes supported by OneXPlayer hardware.
        OneXPlayer硬件支持的RGB模式列表。
        
        Includes basic modes plus OXP brand preset effects.
        包括基础模式加上OXP品牌预设效果。
        """
        modes = [
            RGBMode.Disabled,
            RGBMode.Solid,
            RGBMode.Rainbow,
        ]
        
        # Add OXP preset modes if device supports RGB
        # 如果设备支持RGB，添加OXP预设模式
        if self._config and self._config.rgb:
            modes.extend([
                RGBMode.OXP_MONSTER_WOKE,
                RGBMode.OXP_FLOWING,
                RGBMode.OXP_SUNSET,
                RGBMode.OXP_NEON,
                RGBMode.OXP_DREAMY,
                RGBMode.OXP_CYBERPUNK,
                RGBMode.OXP_COLORFUL,
                RGBMode.OXP_AURORA,
                RGBMode.OXP_SUN,
            ])
        
        return modes

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for OneXPlayer devices.
        获取OneXPlayer设备每个支持的RGB模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping RGB modes to their capabilities.
        """
        capabilities = super().get_mode_capabilities()
        
        # Rainbow mode supports speed control
        # Rainbow模式支持速度控制
        capabilities[RGBMode.Rainbow] = RGBModeCapabilities(
            mode=RGBMode.Rainbow,
            color=False,
            color2=False,
            speed=True,
        )
        
        # Battery mode supports brightness control
        # 电池模式支持亮度控制
        capabilities[RGBMode.Battery] = RGBModeCapabilities(
            mode=RGBMode.Battery,
            color=False,
            color2=False,
            speed=False,
            brightness=True,
        )
        
        # All OXP preset modes support brightness control
        # 所有OXP预设模式都支持亮度控制
        oxp_modes = [
            RGBMode.OXP_MONSTER_WOKE,
            RGBMode.OXP_FLOWING,
            RGBMode.OXP_SUNSET,
            RGBMode.OXP_NEON,
            RGBMode.OXP_DREAMY,
            RGBMode.OXP_CYBERPUNK,
            RGBMode.OXP_COLORFUL,
            RGBMode.OXP_AURORA,
            RGBMode.OXP_SUN,
        ]
        
        for mode in oxp_modes:
            capabilities[mode] = RGBModeCapabilities(
                mode=mode,
                color=False,
                color2=False,
                speed=False,
                brightness=True,
            )
        
        return capabilities

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
    ) -> None:
        """
        Set hardware RGB color with protocol-aware routing.
        使用协议感知路由设置硬件RGB颜色。
        
        Supports HID, Serial, and Mixed (HID+Serial) protocols.
        支持HID、串口和混合（HID+串口）协议。
        """
        if not color:
            return
        
        # Use configuration if available, fallback to legacy detection
        # 如果配置可用则使用配置，否则回退到传统检测
        if self._config:
            if self._config.protocol == OXPProtocol.SERIAL:
                self.set_onex_color_serial(color, mode)
            elif self._config.protocol == OXPProtocol.MIXED:
                # F1 series: HID for sticks, Serial for secondary zone
                # F1系列：HID控制摇杆，串口控制副区域
                self.set_onex_color_hid(color, mode)
                if self._config.rgb_secondary and color2:
                    self.set_onex_color_serial(color2, mode)
            else:
                # HID_V1, HID_V2, HID_V1_G1
                self.set_onex_color_hid(color, mode)
        else:
            # Legacy fallback
            # 传统回退
            if "ONEXPLAYER X1" in PRODUCT_NAME:
                self.set_onex_color_serial(color, mode)
            else:
                self.set_onex_color_hid(color, mode)

    def set_onex_color_hid(self, color: Color, mode: RGBMode | None = None) -> None:
        """
        Set RGB color via HID protocol with retry logic.
        通过HID协议设置RGB颜色，带重试逻辑。
        
        Args:
            color: RGB color
            mode: RGB mode (defaults to Solid if None)
        """
        if mode is None:
            mode = RGBMode.Solid
            
        max_retries = 3
        retry_delay = 1  # seconds
        for retry in range(max_retries + 1):
            if retry > 0:
                logger.info(f"Retry attempt {retry}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff | 指数退避

            ledDevice = OneXLEDDeviceHID(
                [XFLY_VID, X1_MINI_VID],
                [XFLY_PID, X1_MINI_PID],
                [XFLY_PAGE, X1_MINI_PAGE],
                [XFLY_USAGE, X1_MINI_USAGE],
            )
            if ledDevice.is_ready():
                logger.info(f"set_onex_color_hid: color={color}, mode={mode.value}")
                ledDevice.set_led_color_new(color, mode)
                return
            logger.info("set_onex_color_hid: device not ready")

        logger.warning("Failed to set color after all retries")

    def set_onex_color_serial(self, color: Color, mode: RGBMode | None = None) -> None:
        """
        Set RGB color via Serial protocol.
        通过串口协议设置RGB颜色。
        
        Args:
            color: RGB color
            mode: RGB mode (defaults to Solid if None)
        """
        if mode is None:
            mode = RGBMode.Solid
            
        try:
            ledDevice = OneXLEDDeviceSerial()
            if ledDevice.is_ready():
                logger.info(f"set_onex_color_serial: color={color}, mode={mode.value}")
                ledDevice.set_led_color(color, mode)
        except Exception as e:
            logger.error(e, exc_info=True)
