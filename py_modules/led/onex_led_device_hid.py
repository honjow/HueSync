import time
from collections import deque
from enum import Enum
from itertools import chain, repeat
from typing import Sequence

import lib_hid as hid
from config import logger
from utils import Color, RGBMode

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
        # 命令队列系统，确保可靠的命令传输
        self._cmd_queue = deque(maxlen=10)
        self._next_send = 0
        self._write_delay = 0.05  # 50ms delay between commands
        
        # Device state tracking
        # 设备状态跟踪
        self._initialized = False
        self._protocol = Protocol.UNKNOWN

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
        
        V1 protocol (X1 Mini) requires button mapping and intercept setup.
        V2 protocol (XFly) typically doesn't need initialization.
        
        V1协议（X1 Mini）需要按键映射和拦截设置。
        V2协议（XFly）通常不需要初始化。
        """
        if self._initialized:
            return
        
        if self._protocol == Protocol.X1_MINI:
            from .hhd.oxp_hid_v1 import INITIALIZE
            
            logger.info("Initializing X1 Mini device (HID v1)...")
            for cmd in INITIALIZE:
                self._queue_command(cmd)
            
            # Flush initialization commands immediately
            # 立即发送初始化命令
            self._flush_queue()
            logger.info("X1 Mini initialization complete")
        else:
            logger.info(f"No initialization needed for protocol: {self._protocol}")
        
        self._initialized = True
    
    def _queue_command(self, cmd: bytes) -> None:
        """
        Add command to queue for sending.
        将命令添加到发送队列。
        
        Args:
            cmd: Command bytes to send
        """
        self._cmd_queue.append(cmd)
    
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
            # Wait for minimum delay between commands
            # 等待命令之间的最小延迟
            curr = time.perf_counter()
            if curr < self._next_send:
                time.sleep(self._next_send - curr)
            
            # Send command
            cmd = self._cmd_queue.popleft()
            try:
                cmd_hex = "".join([f"{x:02X}" for x in cmd])
                logger.debug(f"OXP HID write: {cmd_hex}")
                self.hid_device.write(cmd)
                self._next_send = time.perf_counter() + self._write_delay
            except Exception as e:
                logger.error(f"Failed to write command: {e}", exc_info=True)
                return False
        
        return True

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
        logger.info(f"msg={msg_hex}")
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
    ) -> bool:
        """
        Set LED color and mode with improved protocol handling.
        使用改进的协议处理设置LED颜色和模式。
        
        Args:
            main_color: RGB color values
            mode: RGB mode (Disabled, Solid, Rainbow, or OXP presets)
            
        Returns:
            bool: True if successful
        """
        if not self.is_ready():
            return False

        if self._protocol == Protocol.X1_MINI:
            from .hhd.oxp_hid_v1 import gen_rgb_mode, gen_rgb_solid
        else:
            from .hhd.oxp_hid_v2 import gen_rgb_mode, gen_rgb_solid

        # Map RGBMode to hardware command
        # 将RGBMode映射到硬件命令
        if mode == RGBMode.Disabled:
            cmd: bytes = gen_rgb_solid(0, 0, 0)
        elif mode == RGBMode.Solid:
            cmd: bytes = gen_rgb_solid(main_color.R, main_color.G, main_color.B)
        elif mode == RGBMode.Rainbow:
            cmd: bytes = gen_rgb_mode("neon")
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
            return False

        if self.hid_device is None:
            return False
        
        # Use command queue for reliable delivery
        # 使用命令队列确保可靠传输
        self._queue_command(cmd)
        return self._flush_queue()
