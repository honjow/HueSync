import lib_hid as hid
from utils import Color, RGBMode
from config import logger
from typing import Sequence
from .hhd.hhd_legino_go_s_hid import rgb_multi_load_settings, rgb_enable


class LegionGoLEDDeviceHID:
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
                logger.debug(
                    f"Found device: {device}, \npath: {device['path']}, \ninterface: {device['interface_number']}"
                )
                return True
        return False

    def set_led_color(
        self,
        main_color: Color,
        mode: RGBMode,
        secondary_color: Color | None = None,
    ) -> bool:
        if not self.is_ready():
            return False

        logger.debug(
            f">>>> set_legion_go_color: mode={mode} color={main_color} secondary={secondary_color}"
        )

        brightness = 1
        speed = 1
        rgb_mode = None

        if mode == RGBMode.Disabled:
            rgb_mode = None

        elif mode == RGBMode.Solid:
            if main_color.R == 0 and main_color.G == 0 and main_color.B == 0:
                rgb_mode = None
            else:
                rgb_mode = "solid"

        elif mode == RGBMode.Rainbow:
            # rainbow
            rgb_mode = "dynamic"

        elif mode == RGBMode.Pulse:
            # pulse
            rgb_mode = "pulse"

        elif mode == RGBMode.Spiral:
            # spiral
            rgb_mode = "spiral"

        else:
            return False

        if rgb_mode:
            reps = rgb_multi_load_settings(
                rgb_mode,
                0x03,
                main_color.R,
                main_color.G,
                main_color.B,
                brightness,
                speed,
                self.prev_mode != rgb_mode,
            )

        else:
            reps = [rgb_enable(False)]


        for r in reps:
            msg_hex = ",".join([f"{x:02X}" for x in r])
            logger.debug(f"msg_hex: {msg_hex}")
            self.hid_device.write(r)

        # self.hid_device.close()

        return True
