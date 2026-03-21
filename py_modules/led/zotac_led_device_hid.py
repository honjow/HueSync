"""Zotac RGB HID implementation.

Packet framing and RGB command layout derived from:
- https://github.com/OpenZotacZone/ZotacZone-Drivers/blob/main/driver/hid/zotac-zone-hid-config.c
- https://github.com/OpenZotacZone/ZotacZone-Drivers/blob/main/driver/hid/zotac-zone-hid-rgb.c

Related upstream driver work:
- https://github.com/flukejones/linux/tree/wip/zotac-zone-6.15/drivers/hid/zotac-zone-hid
"""

import lib_hid as hid

from config import logger
from utils import Color

# Packet layout
REPORT_SIZE = 64

HEADER_TAG_POS = 0
SEQUENCE_POS = 2
PAYLOADSIZE_POS = 3
COMMAND_POS = 4
SETTING_POS = 5
VALUE_POS = 6
CRC_H_POS = 0x3E
CRC_L_POS = 0x3F

HEADER_TAG = 0xE1
PAYLOAD_SIZE = 0x3C

# RGB commands and settings
CMD_SAVE_CONFIG = 0xFB
CMD_SET_RGB = 0xAD

SETTING_COLOR = 0x00
SETTING_SPEED = 0x01
SETTING_EFFECT = 0x02
SETTING_BRIGHTNESS = 0x03

# Firmware effect, speed, and brightness values
EFFECT_RAINBOW = 0x00
EFFECT_BREATHE = 0x01
EFFECT_OFF = 0xF0

SPEED_LOW = 0x00
SPEED_MEDIUM = 0x01
SPEED_HIGH = 0x02

BRIGHTNESS_OFF = 0x00
BRIGHTNESS_LOW = 0x19
BRIGHTNESS_MED = 0x32
BRIGHTNESS_HIGH = 0x4B
BRIGHTNESS_MAX = 0x64

# Zotac USB identifiers and physical RGB layout
ZOTAC_VENDOR_IDS = (0x1EE9, 0x1E19)
ZOTAC_PRODUCT_ID = 0x1590
ZOTAC_COMMAND_INTERFACE = 3
ZOTAC_RGB_ZONE_COUNT = 2
ZOTAC_RGB_LEDS_PER_ZONE = 10


def _calc_crc(data: bytes) -> int:
    """Calculate the Zotac command CRC for a 64-byte report."""
    crc = 0
    for index in range(COMMAND_POS, 0x3E):
        h1 = (crc ^ data[index]) & 0xFF
        h2 = h1 & 0x0F
        h3 = (h2 << 4) ^ h1
        h4 = h3 >> 4
        crc = (((((h3 << 1) ^ h4) << 4) ^ h2) << 3) ^ h4 ^ (crc >> 8)
        crc &= 0xFFFF
    return crc


def _build_command(cmd_code: int, setting: int = 0, data: bytes = b"", sequence: int = 0) -> bytes:
    """Build a single Zotac HID command packet."""
    packet = bytearray(REPORT_SIZE)
    packet[HEADER_TAG_POS] = HEADER_TAG
    packet[SEQUENCE_POS] = sequence & 0xFF
    packet[PAYLOADSIZE_POS] = PAYLOAD_SIZE
    packet[COMMAND_POS] = cmd_code
    packet[SETTING_POS] = setting

    if data:
        copy_len = min(len(data), PAYLOAD_SIZE - 2)
        packet[VALUE_POS : VALUE_POS + copy_len] = data[:copy_len]

    crc = _calc_crc(packet)
    packet[CRC_H_POS] = (crc >> 8) & 0xFF
    packet[CRC_L_POS] = crc & 0xFF
    return bytes(packet)


def _select_device_info(devices):
    """Select the best Zotac HID interface, preferring the command interface."""
    matches = [
        device
        for device in devices
        if device.get("vendor_id") in ZOTAC_VENDOR_IDS
        and device.get("product_id") == ZOTAC_PRODUCT_ID
    ]
    if not matches:
        return None

    return sorted(
        matches,
        key=lambda device: (
            device.get("interface_number") != ZOTAC_COMMAND_INTERFACE,
            device.get("interface_number", 999),
        ),
    )[0]


class ZotacLEDDeviceHID:
    """Low-level Zotac RGB transport over the command HID interface."""

    def __init__(self, timeout_ms: int = 250):
        self._timeout_ms = timeout_ms
        self._sequence = 0
        self.hid_device = None

    @staticmethod
    def has_supported_device() -> bool:
        return _select_device_info(list(hid.enumerate())) is not None

    def is_ready(self) -> bool:
        if self.hid_device is not None:
            return True

        device_info = _select_device_info(list(hid.enumerate()))
        if device_info is None:
            logger.debug("No Zotac command interface found via lib_hid")
            return False

        self.hid_device = hid.Device(path=device_info["path"])
        self._sequence = 0
        logger.info(
            f"Opened Zotac command interface path={device_info.get('path')} "
            f"interface={device_info.get('interface_number')}"
        )
        return True

    def close(self) -> None:
        if self.hid_device and hasattr(self.hid_device, "close"):
            self.hid_device.close()
        self.hid_device = None

    def _read_response(self) -> bytes:
        if self.hid_device is None:
            raise RuntimeError("Zotac HID device is not open")

        try:
            response = self.hid_device.read(REPORT_SIZE, self._timeout_ms)
        except TypeError:
            response = self.hid_device.read(REPORT_SIZE)

        if not response:
            raise RuntimeError("Timed out waiting for Zotac HID response")

        response = bytes(response)
        if len(response) < REPORT_SIZE:
            response += bytes(REPORT_SIZE - len(response))
        return response[:REPORT_SIZE]

    def _exchange(self, cmd_code: int, setting: int = 0, data: bytes = b"") -> bytes:
        """Send one command packet and return the matching response packet."""
        if not self.is_ready():
            raise RuntimeError("Zotac command interface is not available")

        packet = _build_command(cmd_code, setting, data, self._sequence)
        self.hid_device.write(packet)
        response = self._read_response()

        if response[COMMAND_POS] != cmd_code:
            raise RuntimeError(
                f"Unexpected Zotac response command: expected 0x{cmd_code:02X}, got 0x{response[COMMAND_POS]:02X}"
            )

        self._sequence = (self._sequence + 1) & 0xFF
        return response

    def _set_rgb(self, setting: int, data: bytes = b"") -> None:
        """Send an RGB-setting command and require a success status response."""
        response = self._exchange(CMD_SET_RGB, setting, data)
        if len(response) <= VALUE_POS or response[VALUE_POS] != 0:
            raise RuntimeError("Zotac RGB command failed")

    def save_config(self) -> None:
        self._exchange(CMD_SAVE_CONFIG)

    def _write_uniform_zone_color(self, setting: int, color: Color) -> None:
        """Mirror the same color payload to both physical Zotac halo zones."""
        for zone_idx in range(ZOTAC_RGB_ZONE_COUNT):
            payload = bytearray([zone_idx, 0x00, 0x00])
            for _ in range(ZOTAC_RGB_LEDS_PER_ZONE):
                payload.extend([color.R, color.G, color.B])
            self._set_rgb(setting, bytes(payload))

    def set_uniform_color(self, color: Color) -> None:
        self._write_uniform_zone_color(SETTING_COLOR, color)

    def set_effect(self, effect: int) -> None:
        self._set_rgb(SETTING_EFFECT, bytes([effect]))

    def set_speed(self, speed: int) -> None:
        self._set_rgb(SETTING_SPEED, bytes([speed]))

    def set_brightness(self, brightness: int) -> None:
        self._set_rgb(SETTING_BRIGHTNESS, bytes([brightness]))

    def apply_disabled(self, brightness: int = None) -> None:
        """Turn the Zotac lighting off and optionally apply a brightness level."""
        self.set_effect(EFFECT_OFF)
        if brightness is not None:
            self.set_brightness(brightness)
        self.save_config()

    def apply_effect(self, effect: int, color: Color, speed: int, brightness: int) -> None:
        """Apply a hardware RGB effect using the standard color/effect/speed/brightness sequence."""
        self.set_uniform_color(color)
        self.set_effect(effect)
        self.set_speed(speed)
        self.set_brightness(brightness)
        self.save_config()
