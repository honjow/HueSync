from typing import Literal, Sequence

import lib_hid as hid
from config import logger
from utils import Color, RGBMode


Controller = Literal["left", "right"]
LegionRgbMode = Literal["solid", "pulse", "dynamic", "spiral"]

# Lenovo VID and Legion Go PIDs (based on HHD reverse engineering)
LEN_VID = 0x17EF
LEN_PIDS = {
    # Legion Go 1
    0x6182: "xinput",
    0x6183: "dinput",
    0x6184: "dual_dinput",
    0x6185: "fps",
    # Legion Go 2/1 with 2025 Firmware
    0x61EB: "xinput",
    0x61EC: "dinput",
    0x61ED: "dual_dinput",
    0x61EE: "fps",
}


def _get_controller(c: Controller) -> int:
    """
    Get controller ID for command.
    获取控制器命令ID。
    
    Args:
        c: Controller side ("left" or "right")
        
    Returns:
        int: Controller ID (0x03 for left, 0x04 for right)
    """
    if c == "left":
        return 0x03
    elif c == "right":
        return 0x04
    raise ValueError(f"Controller '{c}' not supported.")


def _speed_to_value(speed: str) -> float:
    """
    Convert speed string to value (0.0-1.0).
    转换速度字符串为数值（0.0-1.0）。
    
    Args:
        speed: "low", "medium", or "high"
        
    Returns:
        float: Speed value (0.0=slowest, 1.0=fastest)
    """
    speed_map = {
        "low": 0.33,
        "medium": 0.66,
        "high": 1.0,
    }
    return speed_map.get(speed, 0.66)


def rgb_set_profile(
    controller: Controller,
    profile: Literal[1, 2, 3],
    mode: LegionRgbMode,
    red: int,
    green: int,
    blue: int,
    brightness: float = 1.0,
    speed: float = 1.0,
) -> bytes:
    """
    Create RGB profile setting command for Legion Go controller.
    为Legion Go控制器创建RGB配置文件设置命令。
    
    Command format based on HHD reverse engineering:
    基于HHD逆向工程的命令格式：
    [0x05, 0x0C, 0x72, 0x01, controller, mode, R, G, B, brightness, period, profile, 0x01]
    
    Args:
        controller: "left" or "right"
        profile: Profile number (1-3)
        mode: RGB mode ("solid", "pulse", "dynamic", "spiral")
        red, green, blue: Color values (0-255)
        brightness: Brightness (0.0-1.0)
        speed: Animation speed (0.0-1.0)
        
    Returns:
        bytes: Command to send to device
    """
    r_controller = _get_controller(controller)
    assert profile in (1, 2, 3), f"Invalid profile '{profile}' selected."

    # Map mode to hardware value
    mode_map = {
        "solid": 1,
        "pulse": 2,
        "dynamic": 3,
        "spiral": 4,
    }
    r_mode = mode_map.get(mode, 1)

    # Convert brightness: 0.0-1.0 → 0-63
    r_brightness = min(max(int(64 * brightness), 0), 63)
    
    # Convert speed: 0.0-1.0 → period 0-63 (inverted: 1.0=fast=low period)
    r_period = min(max(int(64 * (1 - speed)), 0), 63)

    return bytes([
        0x05,           # Command prefix
        0x0C,           # Command length
        0x72,           # RGB command type
        0x01,           # Subcommand
        r_controller,   # Controller ID (0x03=left, 0x04=right)
        r_mode,         # Mode (1=solid, 2=pulse, 3=dynamic, 4=spiral)
        red,            # Red (0-255)
        green,          # Green (0-255)
        blue,           # Blue (0-255)
        r_brightness,   # Brightness (0-63)
        r_period,       # Period/Speed (0-63, lower=faster)
        profile,        # Profile number (1-3)
        0x01,           # Terminator
    ])


def rgb_load_profile(
    controller: Controller,
    profile: Literal[1, 2, 3],
) -> bytes:
    """
    Load a saved RGB profile on controller.
    在控制器上加载已保存的RGB配置文件。
    
    Args:
        controller: "left" or "right"
        profile: Profile number (1-3)
        
    Returns:
        bytes: Command to send to device
    """
    r_controller = _get_controller(controller)

    return bytes([
        0x05,           # Command prefix
        0x06,           # Command length
        0x73,           # Load profile command
        0x02,           # Subcommand
        r_controller,   # Controller ID
        profile,        # Profile number
        0x01,           # Terminator
    ])


def rgb_enable(controller: Controller, enable: bool) -> bytes:
    """
    Enable or disable RGB on controller.
    启用或禁用控制器上的RGB。
    
    Args:
        controller: "left" or "right"
        enable: True to enable, False to disable
        
    Returns:
        bytes: Command to send to device
    """
    r_controller = _get_controller(controller)
    r_enable = 0x01 if enable else 0x00

    return bytes([
        0x05,           # Command prefix
        0x06,           # Command length
        0x70,           # Enable/disable command
        0x02,           # Subcommand
        r_controller,   # Controller ID
        r_enable,       # Enable (0x01) or disable (0x00)
        0x01,           # Terminator
    ])


def rgb_multi_load_settings(
    mode: LegionRgbMode,
    profile: Literal[1, 2, 3],
    red: int,
    green: int,
    blue: int,
    brightness: float = 1.0,
    speed: float = 1.0,
    init: bool = True,
) -> list[bytes]:
    """
    Load RGB settings on both left and right controllers.
    在左右控制器上加载RGB设置。
    
    This function synchronizes RGB settings across both controllers
    for a unified lighting experience.
    此函数在两个控制器之间同步RGB设置，以获得统一的灯光效果。
    
    Args:
        mode: RGB mode
        profile: Profile number (1-3)
        red, green, blue: Color values (0-255)
        brightness: Brightness (0.0-1.0)
        speed: Animation speed (0.0-1.0)
        init: Whether to load profile (ignored - always loads for old firmware compatibility)
        
    Returns:
        list[bytes]: List of commands to send in sequence
    """
    # Set profile on both controllers
    base = [
        rgb_set_profile("left", profile, mode, red, green, blue, brightness, speed),
        rgb_set_profile("right", profile, mode, red, green, blue, brightness, speed),
    ]

    # Always load and enable for compatibility
    # Note: Old firmware has issues with conditional loading,
    # so we always send load and enable commands (based on HHD implementation)
    return [
        *base,
        rgb_load_profile("left", profile),
        rgb_load_profile("right", profile),
        rgb_enable("left", True),
        rgb_enable("right", True),
    ]


def rgb_multi_disable() -> list[bytes]:
    """
    Disable RGB on both controllers.
    禁用两个控制器上的RGB。
    
    Returns:
        list[bytes]: List of commands to send in sequence
    """
    return [
        rgb_enable("left", False),
        rgb_enable("right", False),
    ]


class LegionGoTabletHID:
    """
    HID communication handler for Legion Go tablet mode controllers.
    Legion Go平板模式控制器的HID通信处理器。
    
    Supports RGB control for left and right detachable controllers
    through a wireless receiver interface.
    通过无线接收器接口支持左右可拆卸控制器的RGB控制。
    
    Device Parameters (confirmed via HHD reverse engineering):
    - VID: 0x17EF (Lenovo)
    - PIDs: 0x6182-0x6185 (Legion Go 1), 0x61EB-0x61EE (2025 Firmware)
    - Usage Page: 0xFFA0 (NOT 0xFF00)
    - Usage: 0x0001
    """

    def __init__(
        self,
        vid: Sequence[int] = [],
        pid: Sequence[int] = [],
        usage_page: Sequence[int] = [],
        usage: Sequence[int] = [],
        interface: int | None = None,
    ):
        self._vid = vid
        self._pid = pid
        self._usage_page = usage_page
        self._usage = usage
        self.interface = interface
        self.hid_device = None
        self.prev_mode = None
        self.detected_mode = None  # Track detected controller mode

    def is_ready(self) -> bool:
        """
        Check if HID device is ready for communication.
        检查HID设备是否准备好通信。
        
        Returns:
            bool: True if device is found and ready
        """
        if self.hid_device:
            return True

        hid_device_list = hid.enumerate()

        for device in hid_device_list:
            logger.debug(f"Checking device: {device}")
            
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
                self.prev_mode = None  # Reset for new device
                
                # Track detected controller mode
                pid = device["product_id"]
                self.detected_mode = LEN_PIDS.get(pid, "unknown")
                
                logger.info(
                    f"Found Legion Go device: "
                    f"PID=0x{pid:04X} (mode={self.detected_mode}), "
                    f"path={device['path']}, "
                    f"interface={device['interface_number']}, "
                    f"usage_page=0x{device['usage_page']:04X}"
                )
                return True
                
        return False

    def set_led_color(
        self,
        mode: RGBMode,
        color: Color,
        brightness: int = 100,
        speed: str = "medium",
        init: bool = False,
    ) -> bool:
        """
        Set LED color and mode on Legion Go controllers.
        在Legion Go控制器上设置LED颜色和模式。
        
        Args:
            mode: RGB mode (Disabled, Solid, Pulse, Rainbow, Spiral)
            color: Color object with R, G, B values
            brightness: Brightness (0-100), converted to 0.0-1.0
            speed: Speed ("low", "medium", "high")
            init: Whether this is an initialization call
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_ready():
            logger.warning("Legion Go device not ready")
            return False

        logger.debug(
            f"set_led_color: mode={mode} color={color} "
            f"brightness={brightness} speed={speed} init={init}"
        )

        # Convert HueSync modes to Legion hardware modes
        legion_mode = None
        reps = None

        if mode == RGBMode.Disabled:
            reps = rgb_multi_disable()
            
        elif mode == RGBMode.Solid:
            if color.R == 0 and color.G == 0 and color.B == 0:
                # Black = disabled
                reps = rgb_multi_disable()
            else:
                legion_mode = "solid"
                
        elif mode == RGBMode.Rainbow:
            # Legion Go firmware calls this mode "dynamic" not "rainbow"
            legion_mode = "dynamic"
            
        elif mode == RGBMode.Pulse:
            legion_mode = "pulse"
            
        elif mode == RGBMode.Spiral:
            legion_mode = "spiral"
        
        else:
            logger.warning(f"Unsupported mode: {mode}")
            return False

        # Generate commands if mode is set
        if legion_mode:
            brightness_f = brightness / 100.0  # Convert 0-100 to 0.0-1.0
            speed_f = _speed_to_value(speed)
            
            # Track mode change for init logic
            mode_changed = self.prev_mode != mode
            
            reps = rgb_multi_load_settings(
                mode=legion_mode,
                profile=3,  # Use profile 3
                red=color.R,
                green=color.G,
                blue=color.B,
                brightness=brightness_f,
                speed=speed_f,
                init=mode_changed or init,
            )
            self.prev_mode = mode

        # Send commands
        if reps:
            for cmd in reps:
                try:
                    self.hid_device.write(cmd)
                except Exception as e:
                    logger.error(f"Failed to write command: {e}", exc_info=True)
                    return False
                    
            logger.info(
                f"Successfully set Legion Go RGB: mode={mode}, "
                f"controller_mode={self.detected_mode}"
            )
            return True
        
        return False

