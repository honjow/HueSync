import time
from collections import deque
from enum import Enum
from itertools import chain, repeat
from typing import Sequence

import lib_hid as hid
from config import logger
from utils import Color, RGBMode


class DelayMarker:
    """
    Marker to insert custom delay in command queue.
    用于在命令队列中插入自定义延迟的标记。
    """
    def __init__(self, duration: float):
        self.duration = duration


# Global flag to track if full initialization has been done
# This matches HHD's behavior (hid_v1.py line 103)
# 全局标志跟踪是否已完成完整初始化
# 这匹配HHD的行为（hid_v1.py第103行）
_init_done = False

# Global RGB state tracking (persistent across device instances)
# This matches HHD's behavior where state persists in the long-running process
# 全局RGB状态跟踪（跨设备实例持久化）
# 这匹配HHD的行为，状态在长时间运行的进程中持久化
# IMPORTANT: Initialize enabled to False to handle case where HHD disabled LEDs
# This ensures we always send enable=True command on first run
# 重要：初始化enabled为False以处理HHD禁用LED的情况
# 这确保第一次运行时总是发送enable=True命令
_global_prev_enabled = False
_global_prev_brightness = None
_global_prev_mode = None
_global_prev_color = None  # Track color changes in Solid mode

# Secondary zone state tracking (to avoid redundant commands)
# 次要区域状态跟踪（避免冗余命令）
_global_prev_secondary_enabled = None
_global_prev_secondary_color = None

"""
convert from https://github.com/Valkirie/HandheldCompanion/blob/main/HandheldCompanion/Devices/OneXPlayer/OneXPlayerOneXFly.cs 
"""

X1_MINI_VID = 0x1A86
X1_MINI_PID = 0xFE00
X1_MINI_PAGE = 0xFF00
X1_MINI_USAGE = 0x0001

XFLY_VID = 0x1A2C
XFLY_PID = 0xB001
XFLY_PAGE = 0xFF01
XFLY_USAGE = 0x0001


class Protocol(Enum):
    X1_MINI = 0
    XFLY = 1
    UNKNOWN = 2


class OneXLEDDeviceHID:
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
        
        # Command queue system for reliable command delivery
        # Supports both command bytes and DelayMarker for variable delays
        # 命令队列系统，确保可靠的命令传输
        # 支持命令字节和DelayMarker以实现可变延迟
        self._cmd_queue = deque(maxlen=20)  # Increased capacity for markers
        self._next_send = 0
        self._default_delay = 0.05  # 50ms default delay between commands
        
        # Device state tracking
        # 设备状态跟踪
        self._initialized = False
        self._protocol = Protocol.UNKNOWN
        
        # RGB state tracking (to detect when LED needs re-enabling)
        # RGB状态跟踪（用于检测LED是否需要重新启用）
        self._prev_enabled = None  # Track if LEDs were previously enabled
        self._prev_brightness = None  # Track previous brightness
        self._prev_mode = None  # Track previous mode to detect changes

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
                logger.info(
                    f"Found OneXPlayer device: VID={device['vendor_id']:#06x}, "
                    f"PID={device['product_id']:#06x}, path={device['path']}"
                )
                
                # Detect protocol and initialize device
                # 检测协议并初始化设备
                self._protocol = self._check_protocol()
                self._initialize_device()
                
                return True
        return False

    def _check_protocol(self) -> Protocol:
        """
        Detect HID protocol version based on VID/PID.
        根据VID/PID检测HID协议版本。
        
        Returns:
            Protocol: Detected protocol (X1_MINI=v1, XFLY=v2, UNKNOWN)
        """
        # Check if any VID/PID matches X1 Mini (v1 protocol)
        if X1_MINI_VID in self._vid and X1_MINI_PID in self._pid:
            return Protocol.X1_MINI
        # Check if any VID/PID matches XFly (v2 protocol)
        if XFLY_VID in self._vid and XFLY_PID in self._pid:
            return Protocol.XFLY
        return Protocol.UNKNOWN
    
    def _initialize_device(self) -> None:
        """
        Send initialization commands to device.
        向设备发送初始化命令。
        
        IMPORTANT: Matches HHD's behavior (hid_v1.py lines 131-142):
        - Full INITIALIZE only sent once globally (first device)
        - Subsequent devices only send gen_intercept(False)
        - This prevents LED flashing and state reset
        
        重要：匹配HHD的行为（hid_v1.py 131-142行）：
        - 完整初始化只全局发送一次（首个设备）
        - 后续设备只发送gen_intercept(False)
        - 这可以防止LED闪烁和状态重置
        
        V1 protocol (X1 Mini) requires button mapping and intercept setup.
        V2 protocol (XFly) typically doesn't need initialization.
        
        V1协议（X1 Mini）需要按键映射和拦截设置。
        V2协议（XFly）通常不需要初始化。
        """
        if self._initialized:
            return
        
        if self._protocol == Protocol.X1_MINI:
            global _init_done
            from .hhd.oxp_hid_v1 import INITIALIZE, gen_intercept
            
            if not _init_done:
                # First time ever: send full initialization
                # 首次：发送完整初始化
                logger.info("First-time initialization of X1 Mini device (full INITIALIZE)")
                for cmd in INITIALIZE:
                    self._queue_command(cmd)
                _init_done = True
            else:
                # Already initialized before: only send intercept
                # 已经初始化过：只发送intercept
                logger.info("X1 Mini device re-connection (gen_intercept only)")
                self._queue_command(gen_intercept(False))
            
            # Flush initialization commands immediately
            # 立即发送初始化命令
            self._flush_queue()
            logger.info("X1 Mini initialization complete")
        else:
            logger.info(f"No initialization needed for protocol: {self._protocol}")
        
        self._initialized = True
    
    def _queue_command(self, cmd: bytes, delay: float | None = None) -> None:
        """
        Add command to queue for sending with optional custom delay.
        将命令添加到发送队列，可选自定义延迟。
        
        Args:
            cmd: Command bytes to send
            delay: Custom delay AFTER this command (seconds).
                   If None, use default delay between commands.
                   If > 0, insert a DelayMarker after this command.
        """
        self._cmd_queue.append(cmd)
        
        # Insert delay marker if custom delay specified
        # 如果指定了自定义延迟，插入延迟标记
        if delay is not None and delay > 0:
            self._cmd_queue.append(DelayMarker(delay))
    
    def _queue_delay(self, duration: float) -> None:
        """
        Insert a standalone delay marker into queue.
        在队列中插入独立的延迟标记。
        
        Args:
            duration: Delay duration in seconds
        """
        if duration > 0:
            self._cmd_queue.append(DelayMarker(duration))
    
    def _flush_queue(self) -> bool:
        """
        Send all queued commands with proper delays.
        按适当延迟发送所有排队的命令。
        
        Returns:
            bool: True if all commands sent successfully
        """
        if not self.hid_device:
            return False
        
        while self._cmd_queue:
            item = self._cmd_queue.popleft()
            
            # Handle delay marker
            # 处理延迟标记
            if isinstance(item, DelayMarker):
                logger.debug(f"[DELAY] Waiting {item.duration}s")
                time.sleep(item.duration)
                continue
            
            # Handle command
            # 处理命令
            cmd = item
            
            # Wait for minimum delay between commands
            # 等待命令之间的最小延迟
            curr = time.perf_counter()
            if curr < self._next_send:
                time.sleep(self._next_send - curr)
            
            # Send command
            try:
                cmd_hex = "".join([f"{x:02X}" for x in cmd])
                logger.debug(f"[WRITE] OXP HID write ({len(cmd)} bytes): {cmd_hex}")
                self.hid_device.write(cmd)
                self._next_send = time.perf_counter() + self._default_delay
            except Exception as e:
                logger.error(f"[WRITE] Failed to write command: {e}, closing device for reconnection", exc_info=True)
                # Close the device so it can be reopened on next call
                # 关闭设备以便下次调用时重新打开
                self._close_device()
                return False
        
        return True
    
    def _close_device(self):
        """
        Close the HID device and reset state.
        关闭HID设备并重置状态。
        """
        if self.hid_device:
            try:
                self.hid_device.close()
            except Exception as e:
                logger.warning(f"Error closing HID device: {e}")
            self.hid_device = None
        self._initialized = False
        # Clear command queue
        self._cmd_queue.clear()

    def set_led_brightness(self, brightness: int) -> bool:
        # OneXFly brightness range is: 0 - 4 range, 0 is off, convert from 0 - 100 % range
        brightness = round(brightness / 20)

        # Check if device is available
        if self.hid_device is None:
            return False

        # Define the HID message for setting brightness.
        msg: bytearray = bytearray([0x00, 0x07, 0xFF, 0xFD, 0x01, 0x05, brightness])

        # Write the HID message to set the LED brightness.
        self.hid_device.write(bytes(msg))

        return True

    def set_led_brightness_new(self, brightness: int) -> bool:
        """
        Set LED brightness with protocol-aware command generation.
        使用协议感知的命令生成设置LED亮度。
        
        Args:
            brightness: Brightness level (0-100)
            
        Returns:
            bool: True if successful
        """
        brightness = round(brightness / 20)
        enabled = True
        brightness_level = "high"
        match brightness:
            case 0:
                enabled = False
            case 1:
                brightness_level = "low"
            case 3:
                brightness_level = "medium"
            case _:
                brightness_level = "high"

        if self._protocol == Protocol.X1_MINI:
            from .hhd.oxp_hid_v1 import gen_brightness

            cmd: bytes = gen_brightness(0, enabled, brightness_level)
        else:
            from .hhd.oxp_hid_v2 import gen_brightness

            cmd: bytes = gen_brightness(enabled, brightness_level)

        if self.hid_device is None:
            return False
        
        # Use command queue for reliable delivery
        # 使用命令队列确保可靠传输
        self._queue_command(cmd)
        return self._flush_queue()

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
    ) -> bool:
        if not self.is_ready():
            return False

        prefix = [0x00, 0x07, 0xFF]
        LEDOption = [0x00]
        rgbData = [0x00]
        suffix = [0x00]

        if mode == RGBMode.Solid:
            led_color = main_color
            LEDOption = [0xFE]
            rgbData = list(repeat([led_color.R, led_color.G, led_color.B], 20))

        elif mode == RGBMode.Rainbow:
            LEDOption = [0x03]
            rgbData = [list(repeat(0x00, 60))]

        else:
            return False

        msg = list(chain(prefix, LEDOption, chain(*rgbData), suffix))
        msg_hex = "".join([f"{x:02X}" for x in msg])
        logger.debug(f"msg={msg_hex}")
        result: bytearray = bytearray(msg)

        if self.hid_device is None:
            return False

        self.hid_device.write(bytes(result))
        # self.hid_device.close()
        return True

    def set_led_color_new(
        self,
        main_color: Color,
        mode: RGBMode,
        brightness: int = 100,
        secondary_color: Color | None = None,
        secondary_enabled: bool = True,  # New parameter: independent secondary zone switch
    ) -> bool:
        """
        Set LED color and mode with improved protocol handling.
        使用改进的协议处理设置LED颜色和模式。
        
        IMPORTANT: This method now sends brightness/enable command first
        to ensure LEDs are enabled before setting colors. This fixes the
        issue where HueSync can't control LEDs after HHD disables them.
        
        重要：此方法现在会先发送亮度/启用命令，确保LED被启用后再设置颜色。
        这修复了HHD禁用LED后HueSync无法控制的问题。
        
        Args:
            main_color: RGB color values
            mode: RGB mode (Disabled, Solid, Rainbow, or OXP presets)
            brightness: Brightness level (0-100)
            secondary_color: Secondary zone RGB color (optional)
            secondary_enabled: Secondary zone on/off state (default: True)
            
        Returns:
            bool: True if successful
        """
        if not self.is_ready():
            return False

        if self._protocol == Protocol.X1_MINI:
            from .hhd.oxp_hid_v1 import gen_brightness, gen_rgb_mode, gen_rgb_solid
        else:
            from .hhd.oxp_hid_v2 import gen_brightness, gen_rgb_mode, gen_rgb_solid

        # WORKAROUND: Use solid black instead of true disabled mode
        # This avoids hardware state transition issues when re-enabling
        # 变通方案：使用纯黑solid模式代替真正的禁用模式
        # 这避免了重新启用时的硬件状态转换问题
        original_mode = mode  # Save original mode for tracking
        is_disabled_mode = mode == RGBMode.Disabled
        if is_disabled_mode:
            # Keep LEDs enabled, but set to black
            # 保持LED启用，但设置为黑色
            logger.debug(f"[WORKAROUND] Converting Disabled mode to Solid Black")
            enabled = True
            mode = RGBMode.Solid
            main_color = Color(0, 0, 0)
        else:
            enabled = True
        
        # Convert brightness to level
        # 转换亮度到等级
        brightness_val = round(brightness / 20)
        brightness_level = "high"
        if brightness_val <= 1:
            brightness_level = "low"
        elif brightness_val <= 3:
            brightness_level = "medium"
        
        # Use global state tracking (persistent across device instances)
        # This is CRITICAL - HHD's state persists because it's a long-running process
        # 使用全局状态跟踪（跨设备实例持久化）
        # 这是关键 - HHD的状态持久化因为它是长时间运行的进程
        global _global_prev_enabled, _global_prev_brightness, _global_prev_mode, _global_prev_color
        
        # Debug logging for state tracking
        # 状态跟踪调试日志
        logger.debug(f"[STATE] Current: enabled={enabled}, brightness={brightness_level}, mode={mode}")
        logger.debug(f"[STATE] Global Previous: enabled={_global_prev_enabled}, brightness={_global_prev_brightness}, mode={_global_prev_mode}")
        logger.debug(f"[STATE] Secondary: enabled={secondary_enabled}, color={secondary_color}")
        
        # ============================================================
        # PRIMARY ZONE CONTROL (Main LED)
        # 主灯区域控制
        # ============================================================
        
        # Track mode changes for workaround logic
        # 跟踪模式变化用于workaround逻辑
        mode_changed = _global_prev_mode != original_mode
        
        # Check if primary zone state changed
        # 检查主灯区域状态是否改变
        primary_state_changed = (
            _global_prev_enabled != enabled or 
            _global_prev_brightness != brightness_level or
            mode_changed
        )
        
        if primary_state_changed:
            logger.debug(f"[PRIMARY] Sending brightness: enabled={enabled}, brightness={brightness_level}")
            
            if self._protocol == Protocol.X1_MINI:
                # V1: gen_brightness(side, enabled, brightness_level)
                # Use side=0 for all primary zones (left + right controllers)
                # V1：gen_brightness(side, enabled, brightness_level)
                # 使用 side=0 控制所有主区域（左右手柄）
                self._queue_command(gen_brightness(0, enabled, brightness_level))
            else:
                # V2: gen_brightness(enabled, brightness_level)
                brightness_cmd = gen_brightness(enabled, brightness_level)
                self._queue_command(brightness_cmd)
            
            _global_prev_enabled = enabled
            _global_prev_brightness = brightness_level

        # Check if we need to send color/mode command for primary zone
        # For Solid mode: send if mode OR color changed
        # For preset modes: send if mode changed
        # 检查是否需要发送主灯区域的颜色/模式命令
        # 对于Solid模式：如果mode或颜色改变则发送
        # 对于预设模式：如果mode改变则发送
        current_color = (main_color.R, main_color.G, main_color.B) if mode == RGBMode.Solid else None
        primary_color_changed = (mode != _global_prev_mode) or (current_color != _global_prev_color)
        
        if primary_color_changed:
            # Map RGBMode to hardware command
            # 将RGBMode映射到硬件命令
            if mode == RGBMode.Solid:
                if self._protocol == Protocol.X1_MINI:
                    cmd: bytes = gen_rgb_solid(main_color.R, main_color.G, main_color.B, side=0x00)
                else:
                    cmd: bytes = gen_rgb_solid(main_color.R, main_color.G, main_color.B)
            # OXP Preset modes
            # OXP预设模式
            elif mode == RGBMode.OXP_MONSTER_WOKE:
                cmd: bytes = gen_rgb_mode("monster_woke")
            elif mode == RGBMode.OXP_FLOWING:
                cmd: bytes = gen_rgb_mode("flowing")
            elif mode == RGBMode.OXP_SUNSET:
                cmd: bytes = gen_rgb_mode("sunset")
            elif mode == RGBMode.OXP_NEON:
                cmd: bytes = gen_rgb_mode("neon")
            elif mode == RGBMode.OXP_DREAMY:
                cmd: bytes = gen_rgb_mode("dreamy")
            elif mode == RGBMode.OXP_CYBERPUNK:
                cmd: bytes = gen_rgb_mode("cyberpunk")
            elif mode == RGBMode.OXP_COLORFUL:
                cmd: bytes = gen_rgb_mode("colorful")
            elif mode == RGBMode.OXP_AURORA:
                cmd: bytes = gen_rgb_mode("aurora")
            elif mode == RGBMode.OXP_SUN:
                cmd: bytes = gen_rgb_mode("sun")
            else:
                logger.warning(f"Unsupported mode: {mode}")
                # Don't return False here, continue to handle secondary zone
                # 不在这里返回False，继续处理次要灯区域
                cmd = None

            if cmd is not None:
                if self.hid_device is None:
                    return False
                
                logger.debug(f"[PRIMARY] Sending color/mode command for mode={mode}")
                self._queue_command(cmd)
                
                # WORKAROUND: If mode changed, resend command for hardware stability
                # 变通方案：如果模式改变，重发命令以确保硬件稳定性
                if mode_changed:
                    logger.debug(f"[WORKAROUND] Mode changed, flushing + waiting + resending")
                    self._flush_queue()
                    time.sleep(0.1)
                    self._queue_command(cmd)
                    self._flush_queue()  # Flush resend immediately to prevent mixing with secondary zone commands
            
            # Update global state tracking
            # 更新全局状态跟踪
            _global_prev_mode = original_mode
            _global_prev_color = current_color
            _global_prev_brightness = brightness_level
            _global_prev_enabled = enabled
        else:
            logger.debug(f"[PRIMARY] No change in color/mode, skipping primary zone command")
        
        # ============================================================
        # SECONDARY ZONE CONTROL (Independent)
        # 次要灯区域控制（独立）
        # ============================================================
        
        # Only process secondary zone if device supports it (V1 protocol only)
        # 仅在设备支持时处理次要灯区域（仅V1协议）
        if self._protocol == Protocol.X1_MINI:
            global _global_prev_secondary_enabled, _global_prev_secondary_color
            
            # Track secondary zone state changes
            # 跟踪副区域状态变化
            secondary_enabled_changed = _global_prev_secondary_enabled != secondary_enabled
            
            # Convert secondary_color to tuple for comparison
            # 将副区域颜色转换为元组用于比较
            secondary_color_tuple = (secondary_color.R, secondary_color.G, secondary_color.B) if secondary_color else None
            secondary_color_changed = _global_prev_secondary_color != secondary_color_tuple
            
            # Send brightness/enable command only if enabled state changed
            # 只在启用状态改变时发送亮度/启用命令
            if secondary_enabled_changed or True:
                self._queue_command(gen_brightness(0x03, secondary_enabled, "high"))
                self._queue_command(gen_brightness(0x04, secondary_enabled, "high"))
                self._queue_delay(0.5)
                logger.info(f"[SECONDARY] Enabled changed: {_global_prev_secondary_enabled} -> {secondary_enabled}")
                _global_prev_secondary_enabled = secondary_enabled
            
            # Send color command if zone is enabled and color changed
            # 只在区域启用且颜色改变时发送颜色命令
            if secondary_enabled and secondary_color and secondary_color_changed:
                self._queue_command(gen_rgb_solid(secondary_color.R, secondary_color.G, secondary_color.B, side=0x03))
                self._queue_command(gen_rgb_solid(secondary_color.R, secondary_color.G, secondary_color.B, side=0x04))
                logger.info(f"[SECONDARY] Color changed: {_global_prev_secondary_color} -> ({secondary_color.R}, {secondary_color.G}, {secondary_color.B})")
                _global_prev_secondary_color = secondary_color_tuple
            elif not secondary_enabled:
                logger.debug(f"[SECONDARY] Zone disabled, skipping color command")
            elif not secondary_color_changed:
                logger.debug(f"[SECONDARY] Color unchanged, skipping color command")
        
        # Flush all commands with proper delays
        # 按适当延迟发送所有命令
        return self._flush_queue()
