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
        
        # Update zones for all modes based on device capability
        # 根据设备能力为所有模式更新zones
        if self._has_secondary_zone():
            for cap in capabilities.values():
                cap.zones = ['primary', 'secondary']
        
        return capabilities
    
    def _has_secondary_zone(self) -> bool:
        """
        Check if device supports secondary RGB zone.
        检查设备是否支持副区域RGB。
        
        Returns:
            bool: True if device has secondary RGB zone
        """
        if not self._config:
            return False
        
        # Check if device config has rgb_secondary flag
        # 检查设备配置是否有 rgb_secondary 标志
        return self._config.rgb_secondary or self._config.protocol == OXPProtocol.HID_V1_G1
    
    def _get_secondary_zone_info(self) -> dict[str, str]:
        """
        Get secondary zone info (id and name_key) based on device type.
        根据设备类型获取副区域信息（id和name_key）。
        
        Returns:
            dict with 'id' and 'name_key'
        """
        if not self._config:
            return {'id': 'secondary', 'name_key': 'ZONE_SECONDARY_GENERIC_NAME'}
        
        # G1 series: center zone (V-shaped LEDs)
        # G1系列：中心区域（V形LED）
        if self._config.protocol == OXPProtocol.HID_V1_G1:
            return {'id': 'secondary', 'name_key': 'ZONE_SECONDARY_CENTER_NAME'}
        
        # NOTE: MIXED protocol (F1) does not support secondary zone
        # Serial is only for buttons, not for RGB control
        # 注意：MIXED协议（F1）不支持副区域
        # 串口仅用于按钮，不用于RGB控制
        # This branch should never be reached for F1 since _has_secondary_zone() returns False
        # F1不应该到达这个分支，因为 _has_secondary_zone() 返回 False
        elif self._config.protocol == OXPProtocol.MIXED:
            return {'id': 'secondary', 'name_key': 'ZONE_SECONDARY_GENERIC_NAME'}
        
        # X1 Air or other devices with rgb_secondary: generic secondary zone
        # X1 Air或其他有rgb_secondary的设备：通用副区域
        else:
            return {'id': 'secondary', 'name_key': 'ZONE_SECONDARY_GENERIC_NAME'}
    
    def get_device_capabilities(self) -> dict:
        """
        Get device hardware capabilities including zone information.
        获取设备硬件能力，包括区域信息。
        
        Returns:
            dict: Device capabilities
        """
        zones = [
            {'id': 'primary', 'name_key': 'ZONE_PRIMARY_NAME'}
        ]
        
        if self._has_secondary_zone():
            zones.append(self._get_secondary_zone_info())
        
        return {
            'zones': zones,
            'power_led': False,
            'suspend_mode': False,
        }

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        zone_colors: dict[str, Color] | None = None,
        zone_enabled: dict[str, bool] | None = None,  # New parameter: zone enable states
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
            zone_colors: Zone color mapping, e.g., {'secondary': Color(r, g, b)}
            zone_enabled: Zone enable states, e.g., {'secondary': True}
            brightness_level: Hardware brightness level ("low", "medium", "high") - used by OXP preset modes
        """
        if not color:
            return
        
        # Extract secondary zone parameters
        # Frontend already filters these based on device capabilities (_has_secondary_zone):
        # - For unsupported devices (X1 Mini): zone_colors and zone_enabled will be None
        # - For supported devices (X1 Air, G1): zone_colors and zone_enabled contain user settings
        # Backend trusts frontend filtering and processes parameters directly without rechecking capabilities
        #
        # WARNING: If secondary zone commands (side=0x03/0x04) are sent to unsupported devices like X1 Mini,
        # the hardware will misapply these commands to the primary joystick LEDs, causing incorrect colors.
        # For example, sending Color(255,0,0) to secondary zone on X1 Mini will turn joysticks red instead
        # of the configured color. Frontend filtering prevents this by ensuring zone_colors/zone_enabled
        # are None for unsupported devices.
        # 
        # 提取副区域参数
        # 前端已根据设备能力 (_has_secondary_zone) 过滤了这些参数：
        # - 不支持的设备（X1 Mini）：zone_colors 和 zone_enabled 为 None
        # - 支持的设备（X1 Air, G1）：zone_colors 和 zone_enabled 包含用户设置
        # 后端信任前端过滤，直接处理参数而不重复检查设备能力
        #
        # 警告：如果向不支持的设备（如 X1 Mini）发送副区域命令（side=0x03/0x04），
        # 硬件会将这些命令错误地应用到主摇杆 LED，导致颜色错误。
        # 例如，向 X1 Mini 的副区域发送 Color(255,0,0) 会导致摇杆变红，而不是配置的颜色。
        # 前端过滤确保不支持的设备的 zone_colors/zone_enabled 为 None，从而避免此问题。
        secondary_color = zone_colors.get('secondary') if zone_colors else None
        secondary_enabled = zone_enabled.get('secondary', True) if zone_enabled else True
        
        # Use configuration if available, fallback to legacy detection
        # 如果配置可用则使用配置，否则回退到传统检测
        if self._config:
            if self._config.protocol == OXPProtocol.SERIAL:
                self.set_onex_color_serial(color, mode, brightness_level)
            elif self._config.protocol == OXPProtocol.MIXED:
                # F1 series: HID V2 for RGB control only (Serial is for buttons only)
                # F1系列：仅使用HID V2控制RGB（串口仅用于按钮）
                # Note: F1 does not support secondary zone
                # 注意：F1不支持副区域
                self.set_onex_color_hid(color, mode, brightness_level, secondary_enabled=secondary_enabled)
            else:
                # HID_V1, HID_V2, HID_V1_G1
                self.set_onex_color_hid(color, mode, brightness_level, secondary_color=secondary_color, secondary_enabled=secondary_enabled)
        else:
            # Legacy fallback
            # 传统回退
            if "ONEXPLAYER X1" in PRODUCT_NAME:
                self.set_onex_color_serial(color, mode, brightness_level)
            else:
                self.set_onex_color_hid(color, mode, brightness_level, secondary_enabled=secondary_enabled)

    def set_onex_color_hid(self, color: Color, mode: RGBMode | None = None, brightness_level: str | None = None, secondary_color: Color | None = None, secondary_enabled: bool = True) -> None:
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
            secondary_color: Secondary zone RGB color (optional)
            secondary_enabled: Secondary zone on/off state (default: True)
        """
        if mode is None:
            mode = RGBMode.Solid
        
        # Determine which VID/PID to use based on device configuration
        # This avoids the need for complex dynamic protocol detection
        # 根据设备配置确定使用哪组VID/PID，避免复杂的动态协议检测
        if self._config and self._config.protocol in [OXPProtocol.HID_V2, OXPProtocol.MIXED]:
            # F1 (MIXED), Mini Pro (HID_V2) use XFLY protocol
            # F1（MIXED）、Mini Pro（HID_V2）使用XFLY协议
            vid, pid = [XFLY_VID], [XFLY_PID]
            page, usage = [XFLY_PAGE], [XFLY_USAGE]
        else:
            # X1 Mini, X1 Air, etc. use X1_MINI protocol
            # X1 Mini、X1 Air等使用X1_MINI协议
            vid, pid = [X1_MINI_VID], [X1_MINI_PID]
            page, usage = [X1_MINI_PAGE], [X1_MINI_USAGE]
        
        # Convert brightness_level to brightness value (0-100)
        # For Solid/Disabled modes: always use "medium" since they use HSV brightness
        # For OXP preset modes (including OXP_CLASSIC): use the brightness_level parameter
        # 将brightness_level转换为亮度值（0-100）
        # Solid/Disabled模式：固定使用"medium"，因为它们使用HSV亮度控制
        # OXP预设模式（包括OXP_CLASSIC）：使用brightness_level参数
        brightness = 100  # Default to high
        if mode == RGBMode.Solid or mode == RGBMode.Disabled:
            # Solid mode uses HSV brightness, use medium hardware brightness level
            # Solid模式使用HSV亮度，使用中等硬件亮度级别
            brightness_level = "medium"
            brightness = 60
        elif brightness_level == "low":
            brightness = 25
        elif brightness_level == "medium":
            brightness = 60
        elif brightness_level == "high":
            brightness = 100
        
        # Handle OXP Classic mode: convert to Solid mode with cherry red
        # IMPORTANT: This conversion happens AFTER brightness_level logic
        # 处理OXP经典模式：转换为樱桃红的Solid模式
        # 重要：此转换在亮度逻辑之后进行
        if mode == RGBMode.OXP_CLASSIC:
            mode = RGBMode.Solid
            # Cherry red: RGB(183, 48, 0) = 0xB7, 0x30, 0x00
            # 樱桃红：RGB(183, 48, 0) = 0xB7, 0x30, 0x00
            color = Color(0xB7, 0x30, 0x00)
        
        # Try to use cached device first
        # 首先尝试使用缓存的设备
        if self._hid_device_cache and self._hid_device_cache.is_ready():
            logger.debug(f"set_onex_color_hid: using cached device, color={color}, mode={mode.value}, brightness_level={brightness_level}, secondary_color={secondary_color}")
            success = self._hid_device_cache.set_led_color_new(color, mode, brightness=brightness, secondary_color=secondary_color, secondary_enabled=secondary_enabled)
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

            ledDevice = OneXLEDDeviceHID(vid, pid, page, usage)
            if ledDevice.is_ready():
                logger.info(f"set_onex_color_hid: created new device, color={color}, mode={mode.value}, brightness_level={brightness_level}, secondary_color={secondary_color}")
                # Cache the device instance for future calls
                # 缓存设备实例供未来调用使用
                self._hid_device_cache = ledDevice
                ledDevice.set_led_color_new(color, mode, brightness=brightness, secondary_color=secondary_color, secondary_enabled=secondary_enabled)
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
        
        # Handle OXP Classic mode: convert to Solid mode with cherry red
        # 处理OXP经典模式：转换为樱桃红的Solid模式
        if mode == RGBMode.OXP_CLASSIC:
            mode = RGBMode.Solid
            # Cherry red: RGB(183, 48, 0) = 0xB7, 0x30, 0x00
            # 樱桃红：RGB(183, 48, 0) = 0xB7, 0x30, 0x00
            color = Color(0xB7, 0x30, 0x00)
            
        try:
            ledDevice = OneXLEDDeviceSerial()
            if ledDevice.is_ready():
                logger.info(f"set_onex_color_serial: color={color}, mode={mode.value}")
                ledDevice.set_led_color(color, mode)
        except Exception as e:
            logger.error(e, exc_info=True)
