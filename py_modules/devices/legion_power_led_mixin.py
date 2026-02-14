"""
Legion Power LED Control Mixin
Legion Go 电源灯控制混入类

Provides power LED control for Legion Go devices with multi-backend fallback.
为 Legion Go 设备提供电源灯控制功能，支持多后端自动降级。

Backend priority | 后端优先级: acpi_call → MMIO → EC I/O port

Author: HueSync Team
License: MIT
"""

from config import logger
from power_led_backend import select_backend


class LegionPowerLEDMixin:
    """
    Mixin class for Legion Go power LED control with automatic backend selection.
    混入类，为 Legion Go 设备提供通过多后端自动选择控制电源灯的功能。

    子类需要定义 | Subclasses must define:
    - POWER_LED_OFFSET: int - EC 寄存器偏移 | EC register offset
    - POWER_LED_BIT: int - 控制位位置 | Control bit position

    可选 | Optional:
    - WMI_LIGHTING_ID: int - acpi_call 使用的 WMI Lighting_ID (默认 0x04)

    Usage:
        class LegionGoLEDDevice(LegionPowerLEDMixin, BaseLEDDevice):
            POWER_LED_OFFSET = 0x52
            POWER_LED_BIT = 5

    Hardware Details | 硬件详情:
    - Legion Go (83E1, 83N0, 83N1): offset=0x52, bit=5 (LEDP in DSDT)
    - Legion Go S (83L3, 83N6, 83Q2, 83Q3): offset=0x10, bit=6 (LPBL in DSDT)
    - Both use inverted logic | 两者都使用反向逻辑: bit=0 means ON(亮), bit=1 means OFF(灭)
    - ECMM/ERAM base address | 基地址: 0xFE0B0300 (Go 和 Go S 一致)
    - WMI path | WMI 路径: \\_SB.GZFD.WMAF, Lighting_ID=0x04 (Go 和 Go S 一致)

    Backend fallback order | 后端降级顺序:
    1. acpi_call  - 官方 WMI 接口 via /proc/acpi/call | Official WMI interface
    2. MMIO       - 内存映射 I/O via /dev/mem (0xFE0B0300 + offset) | Memory-mapped I/O
    3. EC port    - 传统 I/O 端口命令 (0x66/0x62) | Legacy I/O port commands

    References:
    - DSDT analysis from https://github.com/hhd-dev/hwinfo
    - LegionGoRemapper plugin's power LED control implementation
    """

    # 子类必须定义这两个属性 | Subclass must define these
    POWER_LED_OFFSET: int
    POWER_LED_BIT: int

    # 可选: WMI Lighting_ID (默认 0x04, Go 和 Go S 都适用)
    # Optional: WMI Lighting_ID (default 0x04, works for both Go and Go S)
    WMI_LIGHTING_ID: int = 0x04

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 检查子类是否定义了必需的属性 | Check required attributes
        if not hasattr(self, "POWER_LED_OFFSET") or not hasattr(self, "POWER_LED_BIT"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define POWER_LED_OFFSET and POWER_LED_BIT"
            )

        # 选择最佳可用后端 | Select the best available backend
        self._power_led_backend = select_backend(
            offset=self.POWER_LED_OFFSET,
            bit=self.POWER_LED_BIT,
            lighting_id=self.WMI_LIGHTING_ID,
        )
        self._power_led_available = self._power_led_backend is not None

        # 用于 suspend/resume 的状态跟踪 | State tracking for suspend/resume
        self._power_led_state = None

        if self._power_led_available:
            logger.info(
                f"Power LED control available: "
                f"backend={self._power_led_backend.name}, "
                f"offset=0x{self.POWER_LED_OFFSET:02X}, "
                f"bit={self.POWER_LED_BIT}"
            )
        else:
            logger.info("Power LED control not available on this device")

    def set_power_light(self, enabled: bool) -> bool:
        """
        设置电源灯状态
        Set power LED state.

        Uses the selected backend (acpi_call / MMIO / EC port) to control the LED.
        使用选中的后端（acpi_call / MMIO / EC port）来控制 LED。
        Legion Go series uses inverted logic | 反向逻辑: bit=0 → ON(亮), bit=1 → OFF(灭)

        Args:
            enabled (bool): True to turn on, False to turn off | True 开灯, False 关灯

        Returns:
            bool: True if successful, False otherwise | 成功返回 True
        """
        if not self._power_led_available:
            logger.warning(
                "Power LED control not supported on this device. "
                "Make sure you're running as root and on a Legion Go device."
            )
            return False

        try:
            success = self._power_led_backend.set_power_led(enabled)
            if not success:
                logger.warning(
                    f"Power LED set failed via {self._power_led_backend.name}"
                )
            return success
        except Exception as e:
            logger.error(f"Failed to set power light: {e}", exc_info=True)
            return False

    def get_power_light(self) -> bool | None:
        """
        获取电源灯当前状态
        Get current power LED state.

        Returns:
            bool | None:
                - True if LED is on | True 表示亮
                - False if LED is off | False 表示灭
                - None if unavailable or error | None 表示不可用或出错
        """
        if not self._power_led_available:
            return None

        try:
            return self._power_led_backend.get_power_led()
        except Exception as e:
            logger.error(f"Failed to get power light status: {e}", exc_info=True)
            return None

    def get_device_capabilities(self) -> dict:
        """
        Get device capabilities including power LED support.
        获取设备能力，包括电源 LED 支持。

        Returns:
            dict: Device capabilities with power_led field
        """
        # 从父类获取基础能力 | Get base capabilities from parent class
        if hasattr(super(), "get_device_capabilities"):
            base_caps = super().get_device_capabilities()
        else:
            # 如果没有父类实现则使用后备值 | Fallback if no parent implementation
            base_caps = {
                "zones": [{"id": "primary", "name_key": "ZONE_PRIMARY_NAME"}],
                "suspend_mode": True,
            }

        # 用我们的可用性检查覆盖 power_led | Override power_led with our availability check
        base_caps["power_led"] = self._power_led_available
        return base_caps

    def suspend(self, settings: dict = None) -> None:
        """
        Handle suspend for Legion devices with power LED control.
        处理 Legion 设备的睡眠事件及电源灯控制。

        If user enabled "turn off LED on suspend", saves current state and turns off LED.
        如果用户启用了"睡眠时关闭 LED"，保存当前状态并关闭 LED。
        """
        # 调用父类的 suspend（如果存在）| Call parent suspend if exists
        if hasattr(super(), "suspend"):
            super().suspend(settings)

        if not self._power_led_available or not settings:
            return

        # 检查用户是否启用了电源灯睡眠功能 | Check if user enabled power LED suspend feature
        if settings.get("power_led_suspend_off"):
            try:
                # 关闭前保存当前状态 | Save current state before turning off
                self._power_led_state = self.get_power_light()
                if self._power_led_state:
                    self.set_power_light(False)
                    logger.info("Power LED turned off for suspend (Legion)")
            except Exception as e:
                logger.error(
                    f"Failed to handle power LED on suspend: {e}", exc_info=True
                )

    def resume(self, settings: dict = None) -> None:
        """
        Handle resume for Legion devices with power LED control.
        处理 Legion 设备的唤醒事件及电源灯恢复。

        Restores power LED to its previous state if it was on before suspend.
        如果睡眠前电源灯是开启的，则恢复电源灯状态。
        """
        # 调用父类的 resume（如果存在）| Call parent resume if exists
        if hasattr(super(), "resume"):
            super().resume(settings)

        if not self._power_led_available:
            return

        try:
            # 如果睡眠前电源灯是开启的，则恢复 | Restore power LED if it was on before suspend
            if self._power_led_state:
                self.set_power_light(True)
                logger.info("Power LED restored after resume (Legion)")
                # 清除保存的状态 | Clear saved state
                self._power_led_state = None
        except Exception as e:
            logger.error(
                f"Failed to restore power LED on resume: {e}", exc_info=True
            )
