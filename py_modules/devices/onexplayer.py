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
        
        # Cache HID device instance to avoid re-initialization
        # 缓存HID设备实例以避免重复初始化
        self._hid_device_cache = None

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
                RGBMode.OXP_CLASSIC,
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
        # capabilities[RGBMode.Rainbow] = RGBModeCapabilities(
        #     mode=RGBMode.Rainbow,
        #     color=False,
        #     color2=False,
        #     speed=True,
        # )

        # capabilities[RGBMode.Pulse] = RGBModeCapabilities(
        #     mode=RGBMode.Pulse,
        #     color=True,
        #     color2=False,
        #     speed=True,
        # )
        
        # Battery mode supports brightness control
        # 电池模式支持亮度控制
        # capabilities[RGBMode.Battery] = RGBModeCapabilities(
        #     mode=RGBMode.Battery,
        #     color=False,
        #     color2=False,
        #     speed=False,
        #     brightness=True,
        # )
        
        # OXP preset modes: hardware animations with hardware brightness level control
        # Note: brightness_level (not HSV brightness) will be controlled separately
        # OXP预设模式：硬件动画效果，支持硬件亮度级别控制
        # 注意：brightness_level（不是HSV亮度）将单独控制
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
                brightness=False,  # HSV brightness not applicable for hardware presets
                brightness_level=True,  # Hardware brightness level control
            )
        
        # OXP Classic: Cherry red solid color (brand signature color)
        # OXP经典：樱桃红纯色（品牌标志色）
        capabilities[RGBMode.OXP_CLASSIC] = RGBModeCapabilities(
            mode=RGBMode.OXP_CLASSIC,
            color=False,  # Fixed cherry red color
            color2=False,
            speed=False,
            brightness=False,
            brightness_level=True,  # Hardware brightness level control
        )
        
        return capabilities

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
        brightness_level: str | None = None,  # OneXPlayer uses this parameter
        **kwargs,  # Accept other future parameters
    ) -> None:
        """
        Set hardware RGB color with protocol-aware routing.
        使用协议感知路由设置硬件RGB颜色。
        
        Supports HID, Serial, and Mixed (HID+Serial) protocols.
        支持HID、串口和混合（HID+串口）协议。
        
        Args:
            brightness_level: Hardware brightness level ("low", "medium", "high") - used by OXP preset modes
        """
        if not color:
            return
        
        # Handle OXP Classic mode: convert to Solid mode with cherry red
        # 处理OXP经典模式：转换为樱桃红的Solid模式
        if mode == RGBMode.OXP_CLASSIC:
            mode = RGBMode.Solid
            # Cherry red: RGB(183, 48, 0) = 0xB7, 0x30, 0x00
            # 樱桃红：RGB(183, 48, 0) = 0xB7, 0x30, 0x00
            color = Color(0xB7, 0x30, 0x00)
        
        # Use configuration if available, fallback to legacy detection
        # 如果配置可用则使用配置，否则回退到传统检测
        if self._config:
            if self._config.protocol == OXPProtocol.SERIAL:
                self.set_onex_color_serial(color, mode, brightness_level)
            elif self._config.protocol == OXPProtocol.MIXED:
                # F1 series: HID for sticks, Serial for secondary zone
                # F1系列：HID控制摇杆，串口控制副区域
                self.set_onex_color_hid(color, mode, brightness_level)
                if self._config.rgb_secondary and color2:
                    self.set_onex_color_serial(color2, mode, brightness_level)
            else:
                # HID_V1, HID_V2, HID_V1_G1
                self.set_onex_color_hid(color, mode, brightness_level)
        else:
            # Legacy fallback
            # 传统回退
            if "ONEXPLAYER X1" in PRODUCT_NAME:
                self.set_onex_color_serial(color, mode, brightness_level)
            else:
                self.set_onex_color_hid(color, mode, brightness_level)

    def set_onex_color_hid(self, color: Color, mode: RGBMode | None = None, brightness_level: str | None = None) -> None:
        """
        Set RGB color via HID protocol with retry logic.
        通过HID协议设置RGB颜色，带重试逻辑。
        
        IMPORTANT: Uses cached device instance to avoid re-initialization.
        This prevents LED flashing and maintains state across calls.
        
        重要：使用缓存的设备实例以避免重复初始化。
        这可以防止LED闪烁并在调用之间保持状态。
        
        Args:
            color: RGB color
            mode: RGB mode (defaults to Solid if None)
        """
        if mode is None:
            mode = RGBMode.Solid
        
        # Convert brightness_level to brightness value (0-100)
        # Default to "high" (100) if not specified
        # 将brightness_level转换为亮度值（0-100）
        # 如果未指定则默认为"high"（100）
        brightness = 100  # Default to high
        if brightness_level == "low":
            brightness = 33
        elif brightness_level == "medium":
            brightness = 66
        elif brightness_level == "high":
            brightness = 100
        
        # Try to use cached device first
        # 首先尝试使用缓存的设备
        if self._hid_device_cache and self._hid_device_cache.is_ready():
            logger.debug(f"set_onex_color_hid: using cached device, color={color}, mode={mode.value}, brightness_level={brightness_level}")
            success = self._hid_device_cache.set_led_color_new(color, mode, brightness=brightness)
            if success:
                return
            else:
                # Device write failed (possibly disconnected), clear cache and recreate
                # 设备写入失败（可能断开连接），清除缓存并重新创建
                logger.warning("Cached device write failed, clearing cache and recreating device")
                self._hid_device_cache = None
        
        # If no cache or device not ready, create/recreate device
        # 如果没有缓存或设备未就绪，创建/重建设备
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
                logger.info(f"set_onex_color_hid: created new device, color={color}, mode={mode.value}, brightness_level={brightness_level}")
                # Cache the device instance for future calls
                # 缓存设备实例供未来调用使用
                self._hid_device_cache = ledDevice
                ledDevice.set_led_color_new(color, mode, brightness=brightness)
                return
            logger.info("set_onex_color_hid: device not ready")

        logger.warning("Failed to set color after all retries")

    def set_onex_color_serial(self, color: Color, mode: RGBMode | None = None, brightness_level: str | None = None) -> None:
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
