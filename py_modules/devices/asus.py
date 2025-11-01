import threading
import time

from config import PRODUCT_NAME, logger
from id_info import ID_MAP
from led.asus_led_device_hid import AsusLEDDeviceHID
from utils import Color, RGBMode, RGBModeCapabilities

from .led_device import BaseLEDDevice


class AsusLEDDevice(BaseLEDDevice):
    """
    AsusLEDDevice provides control for Asus devices, integrating with specific
    product IDs for tailored settings.

    AsusLEDDevice为Asus设备提供控制，集成特定产品ID以进行定制设置。
    """

    def __new__(cls):
        """
        Factory method to return the appropriate subclass based on device type.
        根据设备类型返回适当的子类的工厂方法。
        """
        # If already a subclass, create directly | 如果已经是子类，直接创建
        if cls is not AsusLEDDevice:
            logger.debug(f"Creating subclass directly: {cls.__name__}")
            return super().__new__(cls)
        
        from config import PRODUCT_NAME, logger as config_logger
        from id_info import ID_MAP
        
        logger.debug(f"Factory pattern: checking PRODUCT_NAME='{PRODUCT_NAME}'")
        
        # Strategy 1: Exact substring match (current behavior)
        # 策略 1：精确子串匹配（当前行为）
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                logger.debug(f"Matched product (exact): {product_name}")
                # Check if it's ROG Ally series | 判断是否是 ROG Ally 系列
                if "Ally" in product_name:
                    logger.info(f"Factory pattern: Detected ROG Ally, returning AllyLEDDevice")
                    from .asus_ally import AllyLEDDevice
                    return super().__new__(AllyLEDDevice)
        
        # Strategy 2: Keyword-based flexible matching for Ally variants
        # 策略 2：基于关键词的灵活匹配（Ally 变体）
        product_upper = PRODUCT_NAME.upper()
        
        # Check for ROG Ally variants with keyword matching (order matters: most specific first)
        # 使用关键词匹配检查 ROG Ally 变体（顺序重要：最具体的优先）
        ally_keywords = [
            ("ROG XBOX ALLY X", "Xbox Ally X"),  # Xbox Ally X (highest priority)
            ("ROG XBOX ALLY", "Xbox Ally"),      # Xbox Ally
            ("ROG ALLY X", "Ally X"),            # Ally X
            ("ROG ALLY", "Ally"),                # Original Ally
        ]
        
        for keyword, description in ally_keywords:
            if keyword in product_upper:
                logger.info(f"Factory pattern: Detected {description} via keyword matching, returning AllyLEDDevice")
                from .asus_ally import AllyLEDDevice
                return super().__new__(AllyLEDDevice)
        
        # Strategy 3: Fallback to base class
        # 策略 3：降级到基类
        logger.debug("Factory pattern: No Ally variant detected, returning base AsusLEDDevice")
        return super().__new__(cls)

    def __init__(self):
        # Prevent re-initialization | 防止重复初始化
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        super().__init__()
        self._current_real_mode: RGBMode = RGBMode.Disabled
        self._hid_device_cache = None  # Cache HID device instance | 缓存HID设备实例
        self._device_lock = threading.Lock()  # Thread safety | 线程安全
        
        # Strategy 1: Try exact match first
        # 策略 1：首先尝试精确匹配
        matched = False
        for product_name, id_info in ID_MAP.items():
            if product_name in PRODUCT_NAME:
                self.id_info = id_info
                matched = True
                logger.info(f"Matched device via ID_MAP: {product_name} (VID: 0x{id_info.vid:04X}, PID: 0x{id_info.pid:04X})")
                break
        
        # Strategy 2: Fallback to keyword matching for compatible ID
        # 策略 2：降级到关键词匹配以查找兼容的 ID
        if not matched:
            product_upper = PRODUCT_NAME.upper()
            
            # Map keywords to ID_MAP keys for lookup (order matters: most specific first)
            # 将关键词映射到 ID_MAP 的 key 进行查找（顺序重要：最具体的优先）
            keyword_to_idmap = [
                ("ROG XBOX ALLY X", "ROG Xbox Ally X RC73X"),  # Use Xbox Ally X config
                ("ROG XBOX ALLY", "ROG Xbox Ally RC73Y"),      # Use Xbox Ally config
                ("ROG ALLY X", "ROG Ally X RC72L"),            # Use Ally X config
                ("ROG ALLY", "ROG Ally RC71L"),                # Use original Ally config
            ]
            
            for keyword, idmap_key in keyword_to_idmap:
                if keyword in product_upper and idmap_key in ID_MAP:
                    self.id_info = ID_MAP[idmap_key]
                    matched = True
                    logger.info(f"Matched device via keyword '{keyword}' -> {idmap_key} (VID: 0x{self.id_info.vid:04X}, PID: 0x{self.id_info.pid:04X})")
                    break
        
        if not matched:
            logger.warning(f"No matching device found for PRODUCT_NAME: {PRODUCT_NAME}")

    def _set_solid_color(self, color: Color) -> None:
        self._set_hardware_color(RGBMode.Solid, color)

    def _get_or_create_device(self) -> AsusLEDDeviceHID | None:
        """
        Get cached device or create new one with retry logic.
        获取缓存的设备或创建新设备（带重试逻辑）。
        
        Returns:
            AsusLEDDeviceHID | None: Device instance or None if failed
        """
        # Try cached device first | 首先尝试缓存的设备
        if self._hid_device_cache and self._hid_device_cache.is_ready():
            logger.debug("Using cached HID device")
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
            
            device = AsusLEDDeviceHID(
                vid=[self.id_info.vid],
                pid=[self.id_info.pid],
                usage_page=[0xFF31],
                usage=[0x0080],
            )
            if device.is_ready():
                logger.debug("Created and cached new HID device")
                self._hid_device_cache = device
                return device
            
            logger.debug(f"Device not ready on attempt {retry + 1}")
        
        logger.warning("Failed to get LED device after all retries")
        return None

    @property
    def hardware_supported_modes(self) -> list[RGBMode]:
        return [
            RGBMode.Disabled,
            RGBMode.Solid,
            RGBMode.Pulse,
            RGBMode.Duality,
            RGBMode.Rainbow,
            RGBMode.Spiral,
        ]

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
                    logger.warning("Failed to get LED device after retries")
                    return
                
                init = self._current_real_mode != mode or init
                logger.debug(
                    f"set_asus_color: mode={mode} color={color} secondary={color2} init={init} speed={speed}"
                )
                
                if mode:
                    if init:
                        # First call: send global initialization | 首次调用：发送全局初始化
                        success = ledDevice.set_led_color(
                            color, RGBMode.Disabled, init=True, global_init=True
                        )
                        if not success:
                            logger.warning("Failed to send init sequence, clearing cache")
                            self._hid_device_cache = None
                            return
                    
                    # Subsequent calls: skip global init | 后续调用：跳过全局初始化
                    success = ledDevice.set_led_color(
                        color, mode, init=init, secondary_color=color2, 
                        speed=speed or "low", global_init=False
                    )
                    
                    if not success:
                        logger.warning("Failed to set LED color, clearing cache")
                        self._hid_device_cache = None
                        return
                        
                self._current_real_mode = mode or RGBMode.Disabled
            except Exception as e:
                logger.error(e, exc_info=True)
                self._hid_device_cache = None  # Clear cache on error | 错误时清除缓存
                raise

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode for Asus devices.
        获取 Asus 设备每个支持的 RGB 模式的功能支持情况。

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
            RGBMode.Spiral: RGBModeCapabilities(
                mode=RGBMode.Spiral,
                color=False,
                color2=False,
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
