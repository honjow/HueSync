import lib_hid as hid
from utils import Color, RGBMode
from config import logger
from typing import Sequence
from .hhd_asus_hid import (
    rgb_set,
    rgb_set_brightness,
    RGB_APPLY,
    RGB_INIT,
    RGB_SET,
)


class AsusLEDDeviceHID:
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
        self.hid_device = None

    def is_ready(self) -> bool:
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
                    f"Found device: {device}, \npath: {device['path']}, \ninterface: {device['interface_number']}"
                )
                return True
        return False

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
        secondary_color: Color | None = None,
        init: bool = False,
        global_init: bool = True,
    ) -> bool:
        if not self.is_ready():
            return False

        logger.debug(
            f">>>> set_asus_color: mode={mode} color={main_color} secondary={secondary_color} init={init}"
        )

        k_direction = "left"
        k_speed = "low"
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
                secondary_color.R,
                secondary_color.G,
                secondary_color.B,
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
        if global_init or init:
            msg = [
                *RGB_INIT,
                *msg,
            ]

        for m in msg:
            self.hid_device.write(m)

        return True
