import threading
import time

from config import logger
from led.legion_led_device_hid import LegionGoLEDDeviceHID
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice
from .legion_power_led_mixin import LegionPowerLEDMixin

GOS_VID = 0x1A86
GOS_XINPUT = 0xE310
GOS_PIDS = {
    GOS_XINPUT: "xinput",
    0xE311: "dinput",
}


class LegionGoSLEDDevice(LegionPowerLEDMixin, BaseLEDDevice):
    """
    LegionGoSLEDDevice provides control for Legion Go S LED devices.
    Includes joystick RGB control (via HID) and power LED control (via EC).
    
    Supported models: 83L3, 83N6, 83Q2, 83Q3 (Legion Go S)
    """
    
    # Power LED configuration for Legion Go S
    # EC register offset and bit position for power LED control
    # Reference: DSDT analysis from hwinfo/devices/legion_go_s/acpi/QCCN17WW
    POWER_LED_OFFSET = 0x10  # LPBL field in EC memory
    POWER_LED_BIT = 6        # Bit 6 controls power LED

    def __init__(self):
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Solid
        self._hid_device_cache = None  # Cache HID device instance | 缓存HID设备实例
        self._device_lock = threading.Lock()  # Thread safety | 线程安全

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

    def _get_or_create_device(self) -> LegionGoLEDDeviceHID | None:
        """
        Get cached device or create new one with retry logic.
        获取缓存的设备或创建新设备（带重试逻辑）。
        
        Returns:
            LegionGoLEDDeviceHID | None: Device instance or None if failed
        """
        # Try cached device first | 首先尝试缓存的设备
        if self._hid_device_cache and self._hid_device_cache.is_ready():
            logger.debug("Using cached Legion Go HID device")
            return self._hid_device_cache
        
        # Clear invalid cache | 清除无效缓存
        if self._hid_device_cache:
            logger.debug("Cached device no longer ready, clearing cache")
        self._hid_device_cache = None
        
        # Retry logic (3 attempts with exponential backoff) | 重试逻辑（3次尝试，指数退避）
        max_retries = 3
        retry_delay = 0.5
        for retry in range(max_retries):
            if retry > 0:
                logger.info(f"Retry attempt {retry}/{max_retries-1}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff | 指数退避
            
            device = LegionGoLEDDeviceHID(
                vid=[GOS_VID],
                pid=list(GOS_PIDS),
                usage_page=[0xFFA0],
                usage=[0x0001],
                interface=3,
            )
            if device.is_ready():
                logger.debug("Created and cached new Legion Go HID device")
                self._hid_device_cache = device
                return device
            
            logger.debug(f"Device not ready on attempt {retry + 1}")
        
        logger.warning("Failed to get Legion Go LED device after all retries")
        return None

    def _set_hardware_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        init: bool = False,
        speed: str | None = None,
        **kwargs,  # Accept brightness_level and other future parameters
    ) -> None:
        if not color:
            return

        with self._device_lock:  # Thread safety | 线程安全保护
            try:
                ledDevice = self._get_or_create_device()
                if not ledDevice:
                    logger.warning("Failed to get Legion Go LED device after retries")
                    return
                
                init = self._current_real_mode != mode or init
                logger.debug(
                    f"set_legion_go_color: mode={mode} color={color} secondary={color2} init={init}"
                )
                
                if mode:
                    if init:
                        # First call: send initialization | 首次调用：发送初始化
                        success = ledDevice.set_led_color(
                            main_color=color,
                            mode=RGBMode.Disabled,
                            close_device=False,
                        )
                        if not success:
                            logger.warning("Failed to send init sequence, clearing cache")
                            self._hid_device_cache = None
                            return
                    
                    # Subsequent calls | 后续调用
                    # Note: close_device=True for software modes to allow frequent updates
                    # 注意：软件模式下 close_device=True 以允许高频更新
                    success = ledDevice.set_led_color(
                        main_color=color,
                        mode=mode,
                        secondary_color=color2,
                        close_device=self.is_current_software_mode(),
                    )
                    
                    if not success:
                        logger.warning("Failed to set Legion Go LED color, clearing cache")
                        self._hid_device_cache = None
                        return
                        
                self._current_real_mode = mode or RGBMode.Disabled
            except Exception as e:
                logger.error(e, exc_info=True)
                self._hid_device_cache = None  # Clear cache on error | 错误时清除缓存
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
