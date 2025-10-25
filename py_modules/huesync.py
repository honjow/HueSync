import os

from config import (
    IS_ALLY_LED_SUPPORTED,
    IS_LED_SUPPORTED,
    LED_SUSPEND_MODE_PATH,
    PRODUCT_NAME,
    SYS_VENDOR,
    USE_SYSFS_SUSPEND_MODE,
    logger,
)
from devices.asus import AsusLEDDevice
from devices.asus_ally import AllyLEDDevice
from devices.ayaneo import AyaNeoLEDDevice
from devices.generic import GenericLEDDevice
from devices.gpd import GPDLEDDevice
from devices.led_device import LEDDevice
from devices.legion_go_s import LegionGoSLEDDevice
from devices.legion_go_tablet import LegionGoTabletLEDDevice
from devices.msi import MSILEDDevice
from devices.onexplayer import OneXLEDDevice
from utils import Color, RGBMode, RGBModeCapabilities


class LedControl:
    """
    LedControl is responsible for managing LED device operations such as setting color, mode, and suspend mode.
    It selects the appropriate device based on system vendor and product information.

    LedControl负责管理LED设备的操作，例如设置颜色、模式和挂起模式。
    它根据系统供应商和产品信息选择合适的设备。
    """

    def __init__(self):
        """
        Initializes the LedControl by selecting the appropriate LED device.

        通过选择合适的LED设备来初始化LedControl。
        """
        self.device = self._get_device()

    def _get_device(self) -> LEDDevice:
        """
        Determines and returns the appropriate LEDDevice instance based on system configuration.
        
        Device detection priority (vendor-specific devices before generic):
        1. ASUS Ally (IS_ALLY_LED_SUPPORTED)
        2. AyaNeo (SYS_VENDOR == "AYANEO")
        3. MSI (SYS_VENDOR == "Micro-Star International Co., Ltd.")
        4. ASUS (SYS_VENDOR == "ASUSTeK COMPUTER INC.")
        5. GPD (SYS_VENDOR == "GPD")
        6. OneXPlayer/AOKZOE (SYS_VENDOR matching)
        7. Lenovo Legion Go (SYS_VENDOR == "LENOVO")
        8. Generic (IS_LED_SUPPORTED) - fallback for any device with sysfs LED

        根据系统配置确定并返回合适的LEDDevice实例。
        
        设备检测优先级（厂商特定设备优先于通用设备）：
        1. ASUS Ally (IS_ALLY_LED_SUPPORTED)
        2. AyaNeo (SYS_VENDOR == "AYANEO")
        3. MSI (SYS_VENDOR == "Micro-Star International Co., Ltd.")
        4. ASUS (SYS_VENDOR == "ASUSTeK COMPUTER INC.")
        5. GPD (SYS_VENDOR == "GPD")
        6. OneXPlayer/AOKZOE (SYS_VENDOR 匹配)
        7. Lenovo Legion Go (SYS_VENDOR == "LENOVO")
        8. Generic (IS_LED_SUPPORTED) - 任何带有 sysfs LED 的设备的备用方案

        Returns:
            LEDDevice: An instance of a specific LED device class.
            LEDDevice: 特定LED设备类的实例。

        Raises:
            ValueError: If the device is unsupported.
            ValueError: 如果设备不受支持。
        """
        logger.info(f"SYS_VENDOR: {SYS_VENDOR}")
        logger.info(f"PRODUCT_NAME: {PRODUCT_NAME}")
        logger.info(f"IS_LED_SUPPORTED: {IS_LED_SUPPORTED}")
        logger.info(f"IS_ALLY_LED_SUPPORTED: {IS_ALLY_LED_SUPPORTED}")

        # Priority 1: ASUS devices (including Ally via factory pattern)
        # 优先级 1: ASUS 设备（通过工厂模式包括 Ally）
        if SYS_VENDOR == "ASUSTeK COMPUTER INC.":
            logger.info("Using Asus LED device (SYS_VENDOR)")
            # Factory pattern in AsusLEDDevice will auto-return AllyLEDDevice if needed
            # AsusLEDDevice 中的工厂模式会在需要时自动返回 AllyLEDDevice
            return AsusLEDDevice()
        
        # Priority 2: ASUS Ally with sysfs support (backward compatibility fallback)
        # 优先级 2: 具有 sysfs 支持的 ASUS Ally（向后兼容的备用方案）
        if IS_ALLY_LED_SUPPORTED:
            logger.info("Using Ally LED device (IS_ALLY_LED_SUPPORTED - sysfs fallback)")
            return AllyLEDDevice()
        
        # Priority 3: AyaNeo devices (vendor-specific EC control with sysfs fallback)
        # 优先级 3: AyaNeo 设备（厂商特定的 EC 控制，带 sysfs 回退）
        if SYS_VENDOR == "AYANEO":
            logger.info("Using AyaNeo LED device (SYS_VENDOR)")
            return AyaNeoLEDDevice()
        
        # Priority 4: MSI devices
        # 优先级 4: MSI 设备
        if SYS_VENDOR == "Micro-Star International Co., Ltd.":
            logger.info("Using MSI LED device (SYS_VENDOR)")
            return MSILEDDevice()
        
        # Priority 5: GPD devices
        # 优先级 5: GPD 设备
        if SYS_VENDOR == "GPD" and (PRODUCT_NAME == "G1618-04"):
            logger.info("Using GPD LED device (SYS_VENDOR + PRODUCT_NAME)")
            return GPDLEDDevice()
        
        # Priority 6: OneXPlayer/AOKZOE devices
        # 优先级 6: OneXPlayer/AOKZOE 设备
        if (
            SYS_VENDOR == "ONE-NETBOOK"
            or SYS_VENDOR == "ONE-NETBOOK TECHNOLOGY CO., LTD."
            or SYS_VENDOR == "AOKZOE"
        ):
            logger.info("Using OneX LED device (SYS_VENDOR)")
            return OneXLEDDevice()
        
        # Priority 7: Lenovo Legion Go devices
        # 优先级 7: Lenovo Legion Go 设备
        if SYS_VENDOR == "LENOVO":
            # Check if it's Legion Go (tablet mode) or Legion Go S
            if PRODUCT_NAME in ["83E1", "83N0", "83N1"]:
                logger.info("Using Legion Go (tablet mode) LED device (SYS_VENDOR + PRODUCT_NAME)")
                return LegionGoTabletLEDDevice()
            else:
                logger.info("Using Legion Go S LED device (SYS_VENDOR)")
                return LegionGoSLEDDevice()
        
        # Priority 8: Generic sysfs LED device (fallback)
        # 优先级 8: 通用 sysfs LED 设备（备用方案）
        if IS_LED_SUPPORTED:
            logger.info("Using generic LED device (IS_LED_SUPPORTED)")
            return GenericLEDDevice()
        
        logger.error("Unsupported device: no LED support detected")
        raise ValueError("Unsupported device")

    def set_color(
        self,
        mode: RGBMode | None = None,
        color: Color | None = None,
        color2: Color | None = None,
        zone_colors: dict[str, Color] | None = None,
        zone_enabled: dict[str, bool] | None = None,
        init: bool = False,
        brightness: int | None = None,
        speed: str | None = None,
        brightness_level: str | None = None,
    ) -> None:
        """
        Set the color of the LED
        """
        self.device.set_color(
            mode or RGBMode.Solid,
            color,
            color2,
            zone_colors=zone_colors,
            zone_enabled=zone_enabled,
            init=init,
            brightness=brightness,
            speed=speed,
            brightness_level=brightness_level,
        )

    def get_suspend_mode(self) -> str | None:
        """
        Retrieves the current suspend mode from the LED device if supported.
        如果支持，从LED设备检索当前的挂起模式。
        
        Priority: sysfs > device EC method
        优先级：sysfs > 设备 EC 方法

        Returns:
            str: The current suspend mode, or an empty string if not supported.
            str: 当前的挂起模式，如果不支持则为空字符串。
        """
        # Try sysfs first (kernel driver)
        # 优先尝试 sysfs（内核驱动）
        if USE_SYSFS_SUSPEND_MODE and IS_LED_SUPPORTED and os.path.exists(LED_SUSPEND_MODE_PATH):
            try:
                with open(LED_SUSPEND_MODE_PATH, "r") as f:
                    # eg: [oem] keep off, read the part between []
                    content = f.read().strip()
                    mode = content.split("[")[1].split("]")[0]
                    logger.debug(f"Read suspend mode from sysfs: '{mode}' (raw: '{content}')")
                    return mode
            except Exception as e:
                logger.warning(f"Failed to read suspend mode from sysfs: {e}, falling back to device method")
        
        # Fallback to device method (EC or other implementation)
        # 回退到设备方法（EC 或其他实现）
        try:
            mode = self.device.get_suspend_mode()
            logger.debug(f"Read suspend mode from device method ({self.device.__class__.__name__}): '{mode}'")
            return mode
        except Exception as e:
            logger.debug(f"Device does not support suspend mode: {e}")
            return ""

    def set_suspend_mode(self, mode: str) -> None:
        """
        Sets the suspend mode for the LED device if supported.
        如果支持，为LED设备设置挂起模式。
        
        Priority: sysfs > device EC method
        优先级：sysfs > 设备 EC 方法

        Args:
            mode (str): The suspend mode to set.
            mode (str): 要设置的挂起模式。
        """
        # Validate mode - reject empty values
        # 验证模式 - 拒绝空值
        if not mode or mode.strip() == "":
            logger.warning("Attempted to set empty suspend mode, ignoring")
            return
        
        logger.debug(f"Setting suspend mode: '{mode}' (USE_SYSFS={USE_SYSFS_SUSPEND_MODE}, IS_LED_SUPPORTED={IS_LED_SUPPORTED}, sysfs_exists={os.path.exists(LED_SUSPEND_MODE_PATH) if IS_LED_SUPPORTED else False})")
        
        # Try sysfs first (kernel driver)
        # 优先尝试 sysfs（内核驱动）
        if USE_SYSFS_SUSPEND_MODE and IS_LED_SUPPORTED and os.path.exists(LED_SUSPEND_MODE_PATH):
            try:
                with open(LED_SUSPEND_MODE_PATH, "w") as f:
                    f.write(f"{mode}")
                logger.info(f"Suspend mode set to '{mode}' via sysfs")
                return
            except Exception as e:
                logger.warning(f"Failed to set suspend mode via sysfs: {e}, falling back to device method")
        
        # Fallback to device method (EC or other implementation)
        # 回退到设备方法（EC 或其他实现）
        try:
            logger.debug(f"Setting suspend mode via device method: {self.device.__class__.__name__}")
            self.device.set_suspend_mode(mode)
            logger.info(f"Suspend mode set to '{mode}' via device method")
        except Exception as e:
            logger.error(f"Failed to set suspend mode via device method: {e}", exc_info=True)

    def suspend(self) -> None:
        self.device.suspend()

    def resume(self) -> None:
        self.device.resume()

    def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
        """
        Get the capabilities of each supported RGB mode.
        获取每个支持的 RGB 模式的功能支持情况。

        Returns:
            dict[RGBMode, RGBModeCapabilities]: A dictionary mapping mode names to their capabilities.
                Each capability describes what features (color, brightness, etc.) are supported by the mode.
            dict[RGBMode, RGBModeCapabilities]: 模式名称到其功能支持情况的映射字典。
                每个功能支持情况描述该模式支持的特性（颜色、亮度等）。
        """
        return self.device.get_mode_capabilities()

    def get_device_capabilities(self) -> dict:
        """
        Get device hardware capabilities.
        获取设备硬件能力。

        Returns:
            dict: Device capabilities
            {
                "zones": [{"id": "primary", "name_key": "ZONE_PRIMARY_NAME"}],
                "power_led": bool,  # Whether power LED control is supported
                "suspend_mode": bool,  # Whether suspend mode control is supported
                "device_type": str,  # Device type: "msi", "ayaneo", "generic"
            }
        """
        # Get base capabilities from device
        # 从设备获取基础能力
        base_caps = self.device.get_device_capabilities()
        
        # Add device type for frontend to determine which custom RGB implementation to use
        # 添加设备类型供前端判断使用哪个自定义 RGB 实现
        device_class_name = self.device.__class__.__name__
        logger.debug(f"Device class name: {device_class_name}")
        logger.debug(f"Device capabilities from device: {base_caps}")
        
        # Override device_type if not already set by device
        # 如果设备未设置 device_type，则根据类名设置
        if "device_type" not in base_caps:
            if "MsiLEDDevice" in device_class_name:
                base_caps["device_type"] = "msi"
            elif "AyaNeoLEDDevice" in device_class_name:
                base_caps["device_type"] = "ayaneo"
            elif "AllyLEDDevice" in device_class_name:
                base_caps["device_type"] = "rog_ally"
            else:
                base_caps["device_type"] = "generic"
        
        logger.info(f"Final device capabilities: device_type='{base_caps.get('device_type')}', custom_rgb={base_caps.get('custom_rgb', False)}")
        
        # Add legacy power_led check for backward compatibility
        # 为向后兼容性添加传统的power_led检查
        if "power_led" not in base_caps:
            base_caps["power_led"] = (
                hasattr(self.device, 'set_power_light') and 
                hasattr(self.device, 'get_power_light') and
                getattr(self.device, '_power_led_available', False)
            )
        
        return base_caps

    def set_power_light(self, enabled: bool) -> bool:
        """
        Set power LED state (Legion Go series only).
        设置电源灯状态（仅 Legion Go 系列）。

        Args:
            enabled (bool): True to turn on, False to turn off

        Returns:
            bool: True if successful, False if not supported or failed
        """
        if hasattr(self.device, 'set_power_light'):
            try:
                return self.device.set_power_light(enabled)
            except Exception as e:
                logger.error(f"Failed to set power light: {e}", exc_info=True)
                return False
        else:
            logger.debug("Power LED control not supported on this device")
            return False

    def get_power_light(self) -> bool | None:
        """
        Get power LED state (Legion Go series only).
        获取电源灯状态（仅 Legion Go 系列）。

        Returns:
            bool | None: True if on, False if off, None if not supported or failed
        """
        if hasattr(self.device, 'get_power_light'):
            try:
                return self.device.get_power_light()
            except Exception as e:
                logger.error(f"Failed to get power light: {e}", exc_info=True)
                return None
        else:
            logger.debug("Power LED control not supported on this device")
            return None
