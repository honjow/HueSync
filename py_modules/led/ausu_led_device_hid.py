from typing import Sequence

import lib_hid as hid
from config import logger
from utils import Color, RGBMode

from .hhd.hhd_asus_hid import RGB_APPLY, RGB_INIT, RGB_SET, rgb_set, rgb_set_brightness
from .hhd.hhd_hid_base import buf


def config_rgb(boot: bool = False, charging: bool = False) -> bytes:
    """
    Configure when RGB LEDs are enabled on the device.
    配置设备上RGB LED的启用时机。
    
    This command is CRITICAL for enabling RGB hardware after Windows has disabled it.
    When Windows Armoury Crate disables RGB, it sets the hardware register to 0x00.
    Without sending this command first, all subsequent RGB commands will be ignored.
    
    此命令对于在Windows禁用RGB后重新启用硬件至关重要。
    当Windows Armoury Crate禁用RGB时，它会将硬件寄存器设置为0x00。
    如果不先发送此命令，后续所有RGB命令都会被忽略。
    
    Args:
        boot (bool): Enable RGB during boot/shutdown. Default: False
                     启动/关机时启用RGB。默认：False
        charging (bool): Enable RGB during charging while asleep. Default: False
                        充电休眠时启用RGB。默认：False
    
    Returns:
        bytes: HID command to configure RGB enable state
               用于配置RGB启用状态的HID命令
    
    Command format: [0x5D, 0xD1, 0x09, 0x01, val]
    
    Value bits (val):
        0x02 (0b0010): Enable while awake - ALWAYS included
                       唤醒时启用 - 始终包含
        0x09 (0b1001): Enable during boot/shutdown (0x08 + 0x01)
                       启动/关机时启用
        0x04 (0b0100): Enable during charging sleep
                       充电休眠时启用
        0x0F (0b1111): Enable in all states (0x02 + 0x09 + 0x04)
                       所有状态下启用
        0x00 (0b0000): Disable in all states (what Windows sets)
                       所有状态下禁用（Windows设置的值）
    
    Examples:
        config_rgb()                    # val=0x02, awake only
        config_rgb(boot=True)           # val=0x0B, awake + boot
        config_rgb(charging=True)       # val=0x06, awake + charging
        config_rgb(True, True)          # val=0x0F, always on
    """
    # Always enable while awake (0x02)
    # This is the minimum required for RGB to work
    val = 0x02
    
    if boot:
        val += 0x09  # Add boot/shutdown enable (0x08 + 0x01)
    
    if charging:
        val += 0x04  # Add charging sleep enable
    
    return buf([
        0x5A,  # FEATURE_KBD_DRIVER (CRITICAL: Must be 0x5A, not 0x5D!)
        0xD1,  # Control command group
        0x09,  # RGB configuration command
        0x01,  # Data length (1 byte)
        val    # Configuration value
    ])


class AsusLEDDeviceHID:
    def __init__(
        self,
        vid: Sequence[int] = [],
        pid: Sequence[int] = [],
        usage_page: Sequence[int] = [],
        usage: Sequence[int] = [],
        interface: int | None = None,
        rgb_boot: bool = False,
        rgb_charging: bool = False,
        disable_dynamic_lighting: bool = True,
    ):
        self._vid = vid
        self._pid = pid
        self._usage_page = usage_page
        self._usage = usage
        self.interface = interface
        self.hid_device = None
        
        # RGB configuration
        self.rgb_boot = rgb_boot
        self.rgb_charging = rgb_charging
        self.disable_dynamic_lighting = disable_dynamic_lighting
        self._last_rgb_config = None
        self._last_mode = None  # Track mode changes for optimized initialization
        self._dynamic_lighting_disabled = False  # Track if we've disabled dynamic lighting

    def _disable_ally_x_dynamic_lighting(self) -> None:
        """
        Disable Ally X Windows dynamic lighting that interferes with custom RGB.
        禁用 Ally X Windows 动态灯光，它会干扰自定义 RGB 控制。
        
        This sends a command to the Ally X's dynamic lighting interface (0x00590001)
        to disable the Windows driver's automatic lighting control.
        向 Ally X 的动态灯光接口发送命令以禁用 Windows 驱动的自动灯光控制。
        """
        if not self.disable_dynamic_lighting or self._dynamic_lighting_disabled:
            return
        
        # Ally X PID
        ALLY_X_PID = 0x1B4C
        
        # Only attempt for Ally X devices
        if ALLY_X_PID not in self._pid:
            return
        
        try:
            # Find the dynamic lighting interface (application 0x00590001)
            hid_device_list = hid.enumerate()
            for device in hid_device_list:
                if device["vendor_id"] not in self._vid:
                    continue
                if device["product_id"] != ALLY_X_PID:
                    continue
                
                # Look for the dynamic lighting application ID
                # Note: lib_hid might not expose application ID, so we try the main interface
                try:
                    dynled_device = hid.Device(path=device["path"])
                    # Send disable command: [0x06, 0x01]
                    dynled_device.write(bytes([0x06, 0x01]))
                    dynled_device.close()
                    logger.info("Disabled Ally X dynamic lighting interface")
                    self._dynamic_lighting_disabled = True
                    break
                except Exception as e:
                    # Not the right interface, continue searching
                    logger.debug(f"Failed to disable dynamic lighting on {device['path']}: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Failed to disable Ally X dynamic lighting: {e}")

    def is_ready(self) -> bool:
        if self.hid_device:
            return True

        hid_device_list = hid.enumerate()

        # Check every HID device to find LED device
        for device in hid_device_list:
            logger.debug(f"device: {device}")
            if device["vendor_id"] not in self._vid:
                continue
            if device["product_id"] not in self._pid:
                continue
            if (
                self.interface is not None
                and device["interface_number"] != self.interface
            ):
                continue
            if (
                device["usage_page"] in self._usage_page
                and device["usage"] in self._usage
            ):
                self.hid_device = hid.Device(path=device["path"])
                self._last_rgb_config = None  # Reset config for new device
                self._last_mode = None  # Reset mode tracking for new device
                self._dynamic_lighting_disabled = False  # Reset dynamic lighting state
                logger.debug(
                    f"Found device: {device}, \npath: {device['path']}, \ninterface: {device['interface_number']}"
                )
                # Attempt to disable Ally X dynamic lighting if applicable
                self._disable_ally_x_dynamic_lighting()
                return True
        return False

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
        secondary_color: Color | None = None,
        init: bool = False,
        global_init: bool = False,  # Change default to False | 默认改为False
        speed: str | None = None,
    ) -> bool:
        if not self.is_ready():
            return False

        # Check if mode changed - force initialization on mode change
        # 检查模式是否变化 - 模式变化时强制初始化
        if mode != self._last_mode:
            init = True
            self._last_mode = mode
            logger.debug(f"Mode changed to {mode}, forcing initialization")

        # Check if config_rgb needs to be sent
        current_config = (self.rgb_boot, self.rgb_charging)
        if self._last_rgb_config != current_config:
            logger.debug(
                f"Sending config_rgb command: boot={self.rgb_boot}, charging={self.rgb_charging}"
            )
            try:
                self.hid_device.write(config_rgb(self.rgb_boot, self.rgb_charging))
                self._last_rgb_config = current_config
                init = True  # Force full initialization after config change
            except Exception as e:
                logger.error(f"Failed to send config_rgb command: {e}", exc_info=True)
                return False  # Return failure instead of just logging | 返回失败而非仅记录

        logger.debug(
            f">>>> set_asus_color: mode={mode} color={main_color} secondary={secondary_color} init={init} speed={speed}"
        )

        k_direction = "left"
        k_speed = speed or "low"  # Use dynamic speed parameter, default to "low"
        k_brightness = "medium"

        if mode == RGBMode.Disabled:
            # disabled
            msg = rgb_set(
                "all",
                "disabled",
                k_direction,
                k_speed,
                0,
                0,
                0,
                0,
                0,
                0,
            )

        elif mode == RGBMode.Solid:
            # solid
            msg = rgb_set(
                "all",
                "solid",
                k_direction,
                k_speed,
                main_color.R,
                main_color.G,
                main_color.B,
                0,
                0,
                0,
            )

        elif mode == RGBMode.Rainbow:
            # rainbow
            msg = rgb_set(
                "all",
                "rainbow",
                k_direction,
                k_speed,
                main_color.R,
                main_color.G,
                main_color.B,
                0,
                0,
                0,
            )

        elif mode == RGBMode.Pulse:
            # pulse
            msg = rgb_set(
                "all",
                "pulse",
                k_direction,
                k_speed,
                main_color.R,
                main_color.G,
                main_color.B,
                0,
                0,
                0,
            )

        elif mode == RGBMode.Duality:
            # duality
            msg = rgb_set(
                "all",
                "duality",
                k_direction,
                k_speed,
                main_color.R,
                main_color.G,
                main_color.B,
                secondary_color.R if secondary_color else 0,
                secondary_color.G if secondary_color else 0,
                secondary_color.B if secondary_color else 0,
            )

        elif mode == RGBMode.Spiral:
            # spiral
            msg = rgb_set(
                "all",
                "spiral",
                k_direction,
                k_speed,
                0,
                0,
                0,
                0,
                0,
                0,
            )

        else:
            return False

        msg = [
            rgb_set_brightness(k_brightness),
            *msg,
        ]

        if init:
            # Init should switch modes
            msg = [
                *msg,
                RGB_SET,
                RGB_APPLY,
            ]
        if global_init:  # Only when explicitly requested | 只在明确请求时
            msg = [
                *RGB_INIT,
                *msg,
            ]

        if self.hid_device is None:
            return False

        try:
            for m in msg:
                self.hid_device.write(m)
            return True
        except Exception as e:
            logger.error(f"Failed to write to device: {e}", exc_info=True)
            return False  # Return failure on write error | 写入错误时返回失败

        # if self.hid_device:
        #     self.hid_device.close()
