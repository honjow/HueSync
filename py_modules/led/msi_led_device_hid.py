from typing import Sequence, List
from dataclasses import dataclass
from enum import IntEnum

import lib_hid as hid
from config import logger
from utils import Color, RGBMode

# 0211
ADDR_0163 = {
    "rgb": [0x01, 0xFA],
    "m1": [0x00, 0x7A],
    "m2": [0x01, 0x1F],
}
# 0217
# 0308
ADDR_0166 = {
    "rgb": [0x02, 0x4A],
    "m1": [0x00, 0xBA],
    "m2": [0x01, 0x63],
}
ADDR_DEFAULT = ADDR_0163

# Protocol constants
MAX_DATA_PER_PACKET = 55  # Maximum data bytes per HID packet
MAX_KEYFRAMES = 8  # Maximum number of keyframes
RGB_ZONES_PER_FRAME = 9  # Number of RGB zones per keyframe (8 RGB + ABXY)


class MSIEffect(IntEnum):
    """MSI LED effect types"""

    UNKNOWN_09 = 0x09  # Common effect type from test data


@dataclass
class MSIKeyFrame:
    """Single keyframe containing 9 RGB zones"""

    rgb_zones: List[Color]

    def __post_init__(self):
        if len(self.rgb_zones) != RGB_ZONES_PER_FRAME:
            raise ValueError(f"Must have exactly {RGB_ZONES_PER_FRAME} RGB zones")

    def to_bytes(self) -> bytes:
        """Convert keyframe to bytes (27 bytes total)"""
        data = bytearray()
        for color in self.rgb_zones:
            data.extend([color.R, color.G, color.B])
        return bytes(data)


@dataclass
class MSIRGBConfig:
    """Complete RGB configuration for device protocol"""

    speed: int  # 0-20 (0=fastest, 20=slowest) - device protocol value
    brightness: int  # 0-100
    effect: MSIEffect  # Effect type
    keyframes: List[MSIKeyFrame]  # 1-8 keyframes
    index: int = 0  # Usually 0

    def __post_init__(self):
        if not 0 <= self.speed <= 20:
            raise ValueError("Speed must be 0-20")
        if not 0 <= self.brightness <= 100:
            raise ValueError("Brightness must be 0-100")
        if not 1 <= len(self.keyframes) <= MAX_KEYFRAMES:
            raise ValueError(f"Must have 1-{MAX_KEYFRAMES} keyframes")

    def to_bytes(self) -> bytes:
        """Convert configuration to bytes"""
        data = bytearray()
        # Header: 5 bytes
        data.append(self.index)
        data.append(len(self.keyframes))  # Frame num
        data.append(self.effect)
        data.append(self.speed)
        data.append(self.brightness)

        # Keyframes: 27 bytes each
        for keyframe in self.keyframes:
            data.extend(keyframe.to_bytes())

        return bytes(data)


def normalize_speed(speed: int) -> int:
    """
    Convert intuitive speed value to device protocol value

    Parameters:
    - speed: 0-20, where higher value means faster (intuitive)

    Returns:
    - Device protocol value: 0-20, where 0 is fastest (device protocol)
    """
    if not 0 <= speed <= 20:
        raise ValueError("Speed must be 0-20")
    return 20 - speed


def build_msi_rgb_command(
    config: MSIRGBConfig, addr: dict = ADDR_DEFAULT
) -> List[bytes]:
    """
    Build MSI RGB control command(s) with automatic packet splitting

    Parameters:
    - config: Complete RGB configuration
    - addr: Address mapping (device version dependent)

    Returns:
    - List of HID command packets (1-3 packets depending on data size)
    """
    # Build complete data
    data = config.to_bytes()
    total_size = len(data)

    logger.debug(
        f"Building MSI RGB command: frames={len(config.keyframes)}, "
        f"speed={config.speed}, brightness={config.brightness}, "
        f"total_bytes={total_size}"
    )

    # Calculate base address
    base_addr_high, base_addr_low = addr["rgb"]
    base_addr = (base_addr_high << 8) | base_addr_low

    # Split into packets
    packets = []
    offset = 0
    packet_num = 0

    while offset < total_size:
        # Calculate chunk size for this packet
        chunk_size = min(MAX_DATA_PER_PACKET, total_size - offset)
        chunk_data = data[offset : offset + chunk_size]

        # Calculate current packet's start address
        current_addr = base_addr + offset
        addr_high = (current_addr >> 8) & 0xFF
        addr_low = current_addr & 0xFF

        # Build packet
        packet = (
            bytes(
                [
                    # Preamble
                    0x0F,
                    0x00,
                    0x00,
                    0x3C,
                    # Write first profile
                    0x21,
                    0x01,
                    # Start address
                    addr_high,
                    addr_low,
                    # Data length
                    chunk_size,
                ]
            )
            + chunk_data
        )

        packets.append(packet)

        logger.debug(
            f"Packet {packet_num}: addr=0x{current_addr:04X}, "
            f"size={chunk_size}, offset={offset}"
        )

        offset += chunk_size
        packet_num += 1

    logger.debug(f"Generated {len(packets)} packet(s)")
    return packets


# ===== Convenience Functions =====


def build_solid_color(
    color: Color,
    brightness: int = 100,
    speed: int = 17,
) -> MSIRGBConfig:
    """
    Build config for solid color effect

    Parameters:
    - color: Single color for all zones
    - brightness: 0-100
    - speed: 0-20 (higher = faster, will be converted to device protocol)

    Returns:
    - MSIRGBConfig object ready to send
    """
    keyframe = MSIKeyFrame(rgb_zones=[color] * RGB_ZONES_PER_FRAME)
    return MSIRGBConfig(
        speed=normalize_speed(speed),
        brightness=brightness,
        effect=MSIEffect.UNKNOWN_09,
        keyframes=[keyframe],
    )


def build_pulse_effect(
    colors: List[Color],
    brightness: int = 100,
    speed: int = 10,
) -> MSIRGBConfig:
    """
    Build config for pulse/breathing effect with color transitions

    Parameters:
    - colors: 2-8 colors for gradient (more colors = smoother transition)
    - brightness: 0-100
    - speed: 0-20 (higher = faster pulse, will be converted to device protocol)

    Returns:
    - MSIRGBConfig object ready to send
    """
    if not 2 <= len(colors) <= MAX_KEYFRAMES:
        raise ValueError(f"Pulse effect requires 2-{MAX_KEYFRAMES} colors")

    keyframes = [MSIKeyFrame(rgb_zones=[c] * RGB_ZONES_PER_FRAME) for c in colors]
    return MSIRGBConfig(
        speed=normalize_speed(speed),
        brightness=brightness,
        effect=MSIEffect.UNKNOWN_09,
        keyframes=keyframes,
    )


def build_rainbow_effect(
    brightness: int = 100,
    speed: int = 10,
) -> MSIRGBConfig:
    """
    Build config for rainbow effect - each LED shows different color

    Parameters:
    - brightness: 0-100
    - speed: 0-20 (higher = faster, will be converted to device protocol)

    Returns:
    - MSIRGBConfig object ready to send
    """
    rainbow_colors = [
        Color(255, 0, 0),  # RGB1: Red
        Color(255, 127, 0),  # RGB2: Orange
        Color(255, 255, 0),  # RGB3: Yellow
        Color(0, 255, 0),  # RGB4: Green
        Color(0, 255, 255),  # RGB5: Cyan
        Color(0, 0, 255),  # RGB6: Blue
        Color(127, 0, 255),  # RGB7: Purple
        Color(255, 0, 255),  # RGB8: Magenta
        Color(255, 255, 255),  # ABXY: White
    ]

    keyframe = MSIKeyFrame(rgb_zones=rainbow_colors)
    return MSIRGBConfig(
        speed=normalize_speed(speed),
        brightness=brightness,
        effect=MSIEffect.UNKNOWN_09,
        keyframes=[keyframe],
    )


def build_wave_effect(
    colors: List[Color],
    brightness: int = 100,
    speed: int = 8,
) -> MSIRGBConfig:
    """
    Build config for wave effect - colors flow through LEDs

    Parameters:
    - colors: Base colors for the wave (typically 2-4 colors)
    - brightness: 0-100
    - speed: 0-20 (higher = faster wave, will be converted to device protocol)

    Returns:
    - MSIRGBConfig object ready to send
    """
    # Create multiple keyframes with shifted color patterns
    keyframes = []
    num_frames = 4  # 4 frames for smooth wave animation

    for frame_idx in range(num_frames):
        zones = []
        for zone_idx in range(RGB_ZONES_PER_FRAME):
            # Calculate which color to use based on position and frame
            color_idx = (zone_idx + frame_idx) % len(colors)
            zones.append(colors[color_idx])
        keyframes.append(MSIKeyFrame(rgb_zones=zones))
        logger.debug(f"Keyframe {frame_idx}: {zones}")

    return MSIRGBConfig(
        speed=normalize_speed(speed),
        brightness=brightness,
        effect=MSIEffect.UNKNOWN_09,
        keyframes=keyframes,
    )


def build_spiral_effect(
    right_colors: List[Color],
    left_colors: List[Color],
    bottom_colors: List[Color] | None = None,
    brightness: int = 100,
    speed: int = 15,
    right_clockwise: bool = True,
    left_clockwise: bool = True,
) -> MSIRGBConfig:
    """
    Build config for spiral/rotating effect - colors rotate around joysticks
    构建旋转效果配置 - 颜色在摇杆周围旋转

    The effect generates 4 keyframes for a complete rotation cycle.
    效果生成 4 个关键帧以完成一次完整旋转循环。

    Parameters:
    - right_colors: Colors for right joystick zones (1-4 colors, will be cycled if less than 4)
    - left_colors: Colors for left joystick zones (1-4 colors, will be cycled if less than 4)
    - bottom_colors: Colors for ABXY button area (1-4 colors, will be cycled to 4 frames)
                     If None, defaults to white for all frames
    - brightness: 0-100
    - speed: 0-20 (higher = faster rotation, will be converted to device protocol)
    - right_clockwise: If True, right joystick rotates clockwise; if False, counter-clockwise
    - left_clockwise: If True, left joystick rotates clockwise; if False, counter-clockwise

    Returns:
    - MSIRGBConfig object ready to send

    Zone Layout:
    - Zones 0-3: Right joystick (RGB1-RGB4) - 4 LEDs around the stick
    - Zones 4-7: Left joystick (RGB5-RGB8) - 4 LEDs around the stick
    - Zone 8: ABXY buttons

    Example:
        # Create opposing rotations with pulsing ABXY
        config = build_spiral_effect(
            right_colors=[Color(255, 0, 0), Color(0, 0, 255)],
            left_colors=[Color(0, 255, 0), Color(255, 255, 0)],
            bottom_colors=[Color(255, 255, 255), Color(100, 100, 100)],
            right_clockwise=True,
            left_clockwise=False,
            speed=10
        )
    """
    if not right_colors:
        raise ValueError("right_colors cannot be empty")
    if not left_colors:
        raise ValueError("left_colors cannot be empty")

    # Default ABXY colors to white for all frames if not specified
    if bottom_colors is None:
        bottom_colors = [Color(0, 0, 0)]

    # Fixed 4 frames for complete joystick rotation
    num_frames = 4

    # Expand colors to target count by cycling
    def expand_colors(colors: List[Color], target_count: int) -> List[Color]:
        """Expand color list to target_count by cycling"""
        if len(colors) >= target_count:
            return colors[:target_count]
        result = []
        for i in range(target_count):
            result.append(colors[i % len(colors)])
        return result

    # Ensure we have exactly 4 colors for each joystick
    right_base = expand_colors(right_colors, 4)
    left_base = expand_colors(left_colors, 4)
    # Ensure we have exactly 4 colors for bottom (one per frame)
    bottom_base = expand_colors(bottom_colors, 4)

    # Generate keyframes with rotation
    keyframes = []
    for frame_idx in range(num_frames):
        zones = []

        # Right joystick (zones 0-3): rotate colors based on direction
        for zone_idx in range(4):
            if right_clockwise:
                color_idx = (zone_idx + frame_idx) % 4
            else:
                color_idx = (zone_idx - frame_idx) % 4
            zones.append(right_base[color_idx])

        # Left joystick (zones 4-7): rotate colors based on direction
        for zone_idx in range(4):
            if left_clockwise:
                color_idx = (zone_idx + frame_idx) % 4
            else:
                color_idx = (zone_idx - frame_idx) % 4
            zones.append(left_base[color_idx])

        # ABXY buttons (zone 8): use corresponding frame color
        zones.append(bottom_base[frame_idx])

        keyframes.append(MSIKeyFrame(rgb_zones=zones))

        # Debug log
        direction_str = f"R:{'CW' if right_clockwise else 'CCW'} L:{'CW' if left_clockwise else 'CCW'}"
        logger.debug(
            f"Frame {frame_idx}/4 ({direction_str}): "
            f"Right=[{','.join([f'#{c.to_hex()}' for c in zones[0:4]])}] "
            f"Left=[{','.join([f'#{c.to_hex()}' for c in zones[4:8]])}] "
            f"ABXY=#{zones[8].to_hex()}"
        )

    return MSIRGBConfig(
        speed=normalize_speed(speed),
        brightness=brightness,
        effect=MSIEffect.UNKNOWN_09,
        keyframes=keyframes,
    )


def build_disabled() -> MSIRGBConfig:
    """
    Build config to turn off all LEDs

    Returns:
    - MSIRGBConfig object ready to send
    """
    return build_solid_color(color=Color(0, 0, 0), brightness=0, speed=0)


# ===== Legacy Function =====


def set_rgb_cmd(brightness, red, green, blue, addr: dict = ADDR_DEFAULT) -> bytes:
    """
    Legacy function for building single RGB command packet

    Note: This is kept for reference. New code should use build_solid_color() instead.

    Parameters:
    - brightness: 0-1 (will be scaled to 0-100)
    - red, green, blue: 0-255
    - addr: Address mapping

    Returns:
    - Single command packet (bytes)
    """
    return bytes(
        [
            # Preamble
            0x0F,
            0x00,
            0x00,
            0x3C,
            # Write first profile
            0x21,
            0x01,
            # Start at
            *addr["rgb"],
            # Write 31 bytes
            0x20,
            # Index, Frame num, Effect, Speed, Brightness
            0x00,
            0x01,
            0x09,
            0x03,
            max(0, min(100, int(brightness * 100))),
        ]
    ) + 9 * bytes([red, green, blue])


class MSILEDDeviceHID:
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
        self.device_info = None
        self.addr = None

    def is_ready(self) -> bool:
        if self.hid_device:
            return True

        hid_device_list = hid.enumerate()

        # Check every HID device to find LED device
        for device in hid_device_list:
            if device["vendor_id"] not in self._vid:
                continue
            if device["product_id"] not in self._pid:
                continue
            if (
                self.interface is not None
                and device["interface_number"] != self.interface
            ):
                continue
            logger.debug(f"device: {device}")
            if (
                device["usage_page"] in self._usage_page
                and device["usage"] in self._usage
            ):
                self.hid_device = hid.Device(path=device["path"])
                self.device_info = device
                logger.debug(
                    f"Found device: {device}, \npath: {device['path']}, \ninterface: {device['interface_number']}"
                )
                if self.addr is None:
                    ver = (self.device_info or {}).get("release_number", 0x0)
                    major = ver >> 8
                    logger.debug(
                        f"Device version: {ver:#04x}, major: {major}, addr: {self.addr}"
                    )
                    if (
                        (major == 1 and ver >= 0x0166)
                        or (major == 2 and ver >= 0x0217)
                        or (major >= 3)
                    ):
                        self.addr = ADDR_0166
                    else:
                        self.addr = ADDR_0163
                return True
        return False

    def send_rgb_config(self, config: MSIRGBConfig) -> bool:
        """
        Send RGB configuration to device using new packet building system

        Parameters:
        - config: Complete RGB configuration

        Returns:
        - True if successful, False otherwise
        """
        if not self.is_ready():
            logger.error("Device not ready")
            return False

        try:
            packets = build_msi_rgb_command(config, self.addr or ADDR_DEFAULT)

            for i, packet in enumerate(packets):
                msg_hex = "-".join([f"{x:02X}" for x in packet])
                logger.debug(f"Sending packet {i+1}/{len(packets)}: {msg_hex}")

                if self.hid_device:
                    self.hid_device.write(packet)

            logger.info(
                f"Successfully sent RGB config: {len(config.keyframes)} frames, "
                f"{len(packets)} packet(s)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send RGB config: {e}")
            return False
        finally:
            if self.hid_device:
                self.hid_device.close()
                self.hid_device = None

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
        secondary_color: Color | None = None,
        init: bool = False,
        brightness: int = 100,
        speed: int = 15,
    ) -> bool:
        """
        Set LED color using RGBMode (legacy interface)

        This is a convenience wrapper that converts RGBMode to MSIRGBConfig
        using the build_* helper functions and calls send_rgb_config internally.

        Parameters:
        - main_color: Primary color
        - mode: RGB mode (Disabled, Solid, Pulse, etc.)
        - secondary_color: Secondary color (for Pulse mode)
        - init: Initialization flag (unused)
        - brightness: Brightness level (0-100)
        - speed: Speed level (0-20)

        Returns:
        - True if successful, False otherwise
        """
        logger.debug(
            f"set_led_color: mode={mode} color={main_color} secondary={secondary_color} init={init}"
        )

        try:
            # Build config based on mode using convenience functions
            if mode == RGBMode.Disabled:
                config = build_disabled()

            elif mode == RGBMode.Solid:
                config = build_solid_color(
                    color=main_color, brightness=brightness, speed=speed
                )

            elif mode == RGBMode.Pulse:
                config = build_pulse_effect(
                    colors=[main_color, Color(0, 0, 0)],
                    brightness=brightness,
                    speed=speed,
                )

            elif mode == RGBMode.Rainbow:
                config = build_pulse_effect(
                    colors=[
                        Color.from_hsv(0, 1, 1),
                        Color.from_hsv(60, 1, 1),
                        Color.from_hsv(120, 1, 1),
                        Color.from_hsv(180, 1, 1),
                        Color.from_hsv(240, 1, 1),
                        Color.from_hsv(300, 1, 1),
                    ],
                    brightness=brightness,
                    speed=speed,
                )

            elif mode == RGBMode.Duality:
                config = build_pulse_effect(
                    colors=[
                        main_color,
                        Color(0, 0, 0),
                        secondary_color,
                        Color(0, 0, 0),
                    ],
                    brightness=brightness,
                    speed=speed,
                )
            elif mode == RGBMode.Gradient:
                config = build_pulse_effect(
                    colors=[
                        main_color,
                        secondary_color,
                    ],
                    brightness=brightness,
                    speed=speed,
                )

            elif mode == RGBMode.Spiral:
                config = build_spiral_effect(
                    right_colors=[
                        Color.from_hsv(0, 1, 1),
                        Color.from_hsv(60, 1, 1),
                        Color.from_hsv(120, 1, 1),
                        Color.from_hsv(240, 1, 1),
                    ],
                    left_colors=[
                        Color.from_hsv(0, 1, 1),
                        Color.from_hsv(60, 1, 1),
                        Color.from_hsv(120, 1, 1),
                        Color.from_hsv(240, 1, 1),
                    ],
                    bottom_colors=[
                        Color.from_hsv(0, 1, 1),
                        Color.from_hsv(60, 1, 1),
                        Color.from_hsv(120, 1, 1),
                        Color.from_hsv(240, 1, 1),
                    ],
                    speed=speed,
                    brightness=brightness,
                )

            elif mode == RGBMode.MSI_FROSTFIRE:
                config = build_spiral_effect(
                    right_colors=[
                        Color(255, 0, 0),  # Fire red
                        Color(0, 0, 0),  # Dark
                        Color(0, 0, 255),  # Ice blue
                        Color(0, 0, 0),  # Dark
                    ],
                    left_colors=[
                        Color(0, 0, 255),  # Ice blue
                        Color(0, 0, 0),  # Dark
                        Color(255, 0, 0),  # Fire red
                        Color(0, 0, 0),  # Dark
                    ],
                    bottom_colors=[
                        Color(255, 0, 0),  # Fire red
                        Color(0, 0, 0),  # Dark
                        Color(0, 0, 255),  # Ice blue
                        Color(0, 0, 0),  # Dark
                    ],
                    speed=speed,
                    right_clockwise=True,  # Fire rotates clockwise
                    left_clockwise=False,  # Ice rotates counter-clockwise
                )
            elif mode == RGBMode.OXP_SUN:
                config = build_spiral_effect(
                    right_colors=[
                        Color(255, 0, 0),
                        Color(255, 200, 0),
                        Color(255, 255, 0),
                        Color(255, 255, 0),
                    ],
                    left_colors=[
                        Color(255, 0, 0),
                        Color(255, 200, 0),
                        Color(255, 255, 0),
                        Color(255, 255, 0),
                    ],
                    bottom_colors=[
                        Color(255, 70, 0),
                        Color(255, 100, 0),
                        Color(255, 255, 0),
                        Color(255, 255, 0),
                    ],
                    speed=speed,
                    brightness=brightness,
                )
            else:
                logger.warning(f"Unsupported mode: {mode}")
                return False

            # Delegate to send_rgb_config
            return self.send_rgb_config(config)

        except Exception as e:
            logger.error(f"Failed to set LED color: {e}")
            return False
