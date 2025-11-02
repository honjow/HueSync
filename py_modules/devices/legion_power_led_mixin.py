"""
Legion Power LED Control Mixin
为 Legion Go 设备提供电源灯控制功能的混入类

Author: HueSync Team
License: MIT
"""

from config import logger
from ec import EC


class LegionPowerLEDMixin:
    """
    Mixin class for Legion Go power LED control via EC registers.
    混入类,为 Legion Go 设备提供通过 EC 寄存器控制电源灯的功能。
    
    子类需要定义:
    - POWER_LED_OFFSET: int - EC 寄存器偏移
    - POWER_LED_BIT: int - 控制位位置
    
    Usage:
        class LegionGoLEDDevice(LegionPowerLEDMixin, BaseLEDDevice):
            POWER_LED_OFFSET = 0x52
            POWER_LED_BIT = 5
    
    Hardware Details:
    - Legion Go (83E1, 83N0, 83N1): offset=0x52, bit=5 (LEDP in DSDT)
    - Legion Go S (83L3, 83N6, 83Q2, 83Q3): offset=0x10, bit=6 (LPBL in DSDT)
    - Both use inverted logic: bit=0 means ON, bit=1 means OFF
    
    References:
    - DSDT analysis from https://github.com/hhd-dev/hwinfo
    - LegionGoRemapper plugin's power LED control implementation
    """
    
    # 子类必须定义这两个属性
    POWER_LED_OFFSET: int
    POWER_LED_BIT: int
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 检查子类是否定义了必需的属性
        if not hasattr(self, 'POWER_LED_OFFSET') or not hasattr(self, 'POWER_LED_BIT'):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define POWER_LED_OFFSET and POWER_LED_BIT"
            )
        
        # 检查电源灯控制是否可用
        self._power_led_available = self._check_power_led_support()
        
        # State tracking for suspend/resume
        # 用于 suspend/resume 的状态跟踪
        self._power_led_state = None
        
        if self._power_led_available:
            logger.info(
                f"Power LED control available: offset=0x{self.POWER_LED_OFFSET:02X}, "
                f"bit={self.POWER_LED_BIT}"
            )
        else:
            logger.info("Power LED control not available on this device")
    
    def _check_power_led_support(self) -> bool:
        """
        检查当前设备是否支持电源灯控制
        Check if power LED control is supported on current device.
        
        This method attempts to read the power LED register to verify access.
        If the read fails, it means either:
        1. Not running as root (EC access requires elevated privileges)
        2. EC registers not accessible on this hardware
        3. Wrong register offset for this device model
        
        Returns:
            bool: True if supported, False otherwise
        """
        try:
            # 尝试读取电源灯寄存器
            value = EC.Read(self.POWER_LED_OFFSET)
            logger.debug(
                f"Power LED register check successful: "
                f"offset=0x{self.POWER_LED_OFFSET:02X}, value=0x{value:02X}"
            )
            return True
        except Exception as e:
            logger.debug(f"Power LED register check failed: {e}")
            return False
    
    def set_power_light(self, enabled: bool) -> bool:
        """
        设置电源灯状态
        Set power LED state.
        
        This method controls the power LED by modifying a specific bit in the EC register.
        Legion Go series uses inverted logic where:
        - bit=0 means LED is ON
        - bit=1 means LED is OFF
        
        Args:
            enabled (bool): True to turn on, False to turn off
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> device = LegionGoLEDDevice()
            >>> device.set_power_light(True)   # Turn on power LED
            True
            >>> device.set_power_light(False)  # Turn off power LED
            True
        """
        if not self._power_led_available:
            logger.warning(
                "Power LED control not supported on this device. "
                "Make sure you're running as root and on a Legion Go device."
            )
            return False
        
        try:
            # 读取当前寄存器值
            current = EC.Read(self.POWER_LED_OFFSET)
            bit_mask = 1 << self.POWER_LED_BIT
            
            # Legion Go 系列使用反向逻辑: bit=0 开灯, bit=1 关灯
            # Legion Go series uses inverted logic: bit=0 ON, bit=1 OFF
            if enabled:
                new_value = current & ~bit_mask  # Clear bit = ON
            else:
                new_value = current | bit_mask   # Set bit = OFF
            
            # 写入新值
            EC.Write(self.POWER_LED_OFFSET, new_value)
            
            # 验证写入
            verify = EC.Read(self.POWER_LED_OFFSET)
            success = (verify & bit_mask) == (new_value & bit_mask)
            
            if success:
                logger.debug(
                    f"Power LED set to {'ON' if enabled else 'OFF'}: "
                    f"offset=0x{self.POWER_LED_OFFSET:02X}, "
                    f"bit={self.POWER_LED_BIT}, "
                    f"old=0x{current:02X}, new=0x{new_value:02X}, verify=0x{verify:02X}"
                )
            else:
                logger.warning(
                    f"Power LED write verification failed: "
                    f"expected bit {'0' if enabled else '1'}, got 0x{verify:02X}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to set power light: {e}", exc_info=True)
            return False
    
    def get_power_light(self) -> bool | None:
        """
        获取电源灯当前状态
        Get current power LED state.
        
        This method reads the EC register and extracts the power LED control bit.
        
        Returns:
            bool | None: 
                - True if LED is on
                - False if LED is off
                - None if unavailable or error occurred
                
        Example:
            >>> device = LegionGoLEDDevice()
            >>> status = device.get_power_light()
            >>> if status is not None:
            ...     print(f"Power LED is {'ON' if status else 'OFF'}")
        """
        if not self._power_led_available:
            return None
        
        try:
            # 读取当前寄存器值
            current = EC.Read(self.POWER_LED_OFFSET)
            bit_value = (current >> self.POWER_LED_BIT) & 1
            
            # 反向逻辑: bit=0 表示开启
            # Inverted logic: bit=0 means ON
            is_on = bit_value == 0
            
            logger.debug(
                f"Power LED status: {'ON' if is_on else 'OFF'} "
                f"(offset=0x{self.POWER_LED_OFFSET:02X}, "
                f"bit={self.POWER_LED_BIT}, "
                f"register=0x{current:02X}, bit_value={bit_value})"
            )
            
            return is_on
            
        except Exception as e:
            logger.error(f"Failed to get power light status: {e}", exc_info=True)
            return None
    
    def get_device_capabilities(self) -> dict:
        """
        Get device capabilities including power LED support.
        获取设备能力，包括电源LED支持。
        
        This method extends the base implementation by adding power_led capability.
        If the subclass has its own get_device_capabilities, it will be called first.
        此方法通过添加power_led能力扩展基类实现。
        如果子类有自己的get_device_capabilities，会先调用它。
        
        Returns:
            dict: Device capabilities with power_led field
            {
                "zones": [...],
                "power_led": bool,  # Based on _power_led_available
                "suspend_mode": bool,
            }
        """
        # Get base capabilities from parent class
        # Try to call the next class in MRO (usually BaseLEDDevice)
        # 从父类获取基础能力
        # 尝试调用MRO中的下一个类（通常是BaseLEDDevice）
        if hasattr(super(), 'get_device_capabilities'):
            base_caps = super().get_device_capabilities()
        else:
            # Fallback if no parent implementation
            # 如果没有父类实现则使用后备值
            base_caps = {
                'zones': [{'id': 'primary', 'name_key': 'ZONE_PRIMARY_NAME'}],
                'suspend_mode': True,
            }
        
        # Override power_led with our availability check
        # 用我们的可用性检查覆盖power_led
        base_caps['power_led'] = self._power_led_available
        
        return base_caps
    
    def suspend(self, settings: dict = None) -> None:
        """
        Handle suspend for Legion devices with power LED control.
        处理 Legion 设备的睡眠事件及电源灯控制。
        
        If user enabled "turn off LED on suspend", saves current state and turns off LED.
        如果用户启用了"睡眠时关闭LED"，保存当前状态并关闭LED。
        """
        # Call parent suspend if exists
        # 调用父类的 suspend（如果存在）
        if hasattr(super(), 'suspend'):
            super().suspend(settings)
        
        if not self._power_led_available or not settings:
            return
        
        # Check if user enabled power LED suspend feature
        # 检查用户是否启用了电源灯睡眠功能
        if settings.get('power_led_suspend_off'):
            try:
                # Save current state before turning off
                # 关闭前保存当前状态
                self._power_led_state = self.get_power_light()
                if self._power_led_state:
                    self.set_power_light(False)
                    logger.info("Power LED turned off for suspend (Legion)")
            except Exception as e:
                logger.error(f"Failed to handle power LED on suspend: {e}", exc_info=True)
    
    def resume(self, settings: dict = None) -> None:
        """
        Handle resume for Legion devices with power LED control.
        处理 Legion 设备的唤醒事件及电源灯恢复。
        
        Restores power LED to its previous state if it was on before suspend.
        如果睡眠前电源灯是开启的，则恢复电源灯状态。
        """
        # Call parent resume if exists
        # 调用父类的 resume（如果存在）
        if hasattr(super(), 'resume'):
            super().resume(settings)
        
        if not self._power_led_available:
            return
        
        try:
            # Restore power LED if it was on before suspend
            # 如果睡眠前电源灯是开启的，则恢复
            if self._power_led_state:
                self.set_power_light(True)
                logger.info("Power LED restored after resume (Legion)")
                # Clear saved state
                # 清除保存的状态
                self._power_led_state = None
        except Exception as e:
            logger.error(f"Failed to restore power LED on resume: {e}", exc_info=True)

