from typing import Sequence

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
ADDR_0166 = {
    "rgb": [0x02, 0x4A],
    "m1": [0x00, 0xBA],
    "m2": [0x01, 0x63],
}
ADDR_DEFAULT = ADDR_0163


def set_rgb_cmd(brightness, red, green, blue, addr: dict = ADDR_DEFAULT) -> bytes:
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
                    logger.info(
                        f"Device version: {ver:#04x}, major: {major}, addr: {self.addr}"
                    )
                    if (major == 1 and ver >= 0x0166) or (major == 2 and ver >= 0x0217):
                        self.addr = ADDR_0166
                    else:
                        self.addr = ADDR_0163
                return True
        return False

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
        secondary_color: Color | None = None,
        init: bool = False,
    ) -> bool:
        if not self.is_ready():
            return False

        logger.debug(
            f">>>> set_asus_color: mode={mode} color={main_color} secondary={secondary_color} init={init}"
        )

        if mode == RGBMode.Disabled:
            # disabled
            msg = [set_rgb_cmd(0, 0, 0, 0, self.addr or ADDR_DEFAULT)]

        elif mode == RGBMode.Solid:
            # solid
            msg = [
                set_rgb_cmd(
                    100,
                    main_color.R,
                    main_color.G,
                    main_color.B,
                    self.addr or ADDR_DEFAULT,
                )
            ]

        else:
            return False

        if self.hid_device is None:
            return False

        for m in msg:
            msg_hex = ",".join([f"{x:02X}" for x in m])
            logger.debug(f"msg_hex: {msg_hex}")
            self.hid_device.write(m)

        self.hid_device.close()

        return True
