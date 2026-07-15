import logging
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PY_MODULES = ROOT / "py_modules"
sys.path.insert(0, str(PY_MODULES))

# Keep the unit tests independent from Decky, HID, and host hardware.
config = types.ModuleType("config")
config.DEFAULT_BRIGHTNESS = 100
config.LED_PATH = "/nonexistent"
config.SOFTWARE_EFFECT_UPDATE_RATE = 30.0
config.logger = logging.getLogger("huesync-test")
sys.modules["config"] = config

lib_hid = types.ModuleType("lib_hid")
lib_hid.Device = object
lib_hid.enumerate = lambda: []
sys.modules["lib_hid"] = lib_hid

from devices.legion_go2 import LegionGo2LEDDevice
from devices.legion_go_tablet import LegionGoTabletLEDDevice
from led.legion_go_tablet_hid import rgb_set_profile
from utils import Color, RGBMode


class FakeTabletHID:
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    def is_ready(self):
        return True

    def set_led_color(self, **kwargs):
        self.calls.append(kwargs)
        return True


class LegionGoHIDBrightnessTests(unittest.TestCase):
    def setUp(self):
        FakeTabletHID.calls.clear()

    def _new_device(self):
        with patch(
            "devices.legion_power_led_mixin.select_backend", return_value=None
        ):
            return LegionGoTabletLEDDevice()

    def test_rainbow_and_spiral_forward_numeric_brightness(self):
        device = self._new_device()
        with patch(
            "devices.legion_go_tablet.LegionGoTabletHID", FakeTabletHID
        ):
            for mode in (RGBMode.Rainbow, RGBMode.Spiral):
                for brightness in (0, 25, 100):
                    with self.subTest(mode=mode, brightness=brightness):
                        device.set_color(
                            mode=mode,
                            color=Color(255, 0, 0),
                            brightness=brightness,
                            speed="low",
                        )
                        self.assertEqual(
                            FakeTabletHID.calls[-1]["brightness"], brightness
                        )

    def test_color_modes_do_not_apply_brightness_twice(self):
        device = self._new_device()
        with patch(
            "devices.legion_go_tablet.LegionGoTabletHID", FakeTabletHID
        ):
            for mode in (RGBMode.Solid, RGBMode.Pulse):
                with self.subTest(mode=mode):
                    device.set_color(
                        mode=mode,
                        color=Color(64, 0, 0),
                        brightness=25,
                    )
                    self.assertEqual(FakeTabletHID.calls[-1]["brightness"], 100)

    def test_hid_packets_encode_effect_brightness(self):
        for mode in ("dynamic", "spiral"):
            for brightness, expected in (
                (0.0, 0),
                (0.2, 12),
                (0.5, 32),
                (1.0, 63),
            ):
                with self.subTest(mode=mode, brightness=brightness):
                    packet = rgb_set_profile(
                        "left",
                        3,
                        mode,
                        0,
                        0,
                        0,
                        brightness=brightness,
                    )
                    self.assertEqual(packet[9], expected)


class LegionGo2SysfsBrightnessTests(unittest.TestCase):
    SYSFS_ATTRS = (
        "brightness",
        "effect",
        "effect_index",
        "enabled",
        "mode",
        "mode_index",
        "multi_intensity",
        "multi_max_intensity",
        "profile",
        "speed",
    )

    def _new_device(self, led_path: Path):
        for attr in self.SYSFS_ATTRS:
            (led_path / attr).write_text("")
        (led_path / "effect_index").write_text(
            "monocolor breathe chroma rainbow\n"
        )
        (led_path / "mode_index").write_text("dynamic custom\n")
        (led_path / "max_brightness").write_text("100\n")
        (led_path / "multi_max_intensity").write_text("100 100 100\n")

        with (
            patch("devices.sysfs_led_mixin.LED_PATH", str(led_path)),
            patch(
                "devices.legion_power_led_mixin.select_backend",
                return_value=None,
            ),
        ):
            return LegionGo2LEDDevice()

    def test_native_effects_map_brightness_and_speed(self):
        with TemporaryDirectory() as temp_dir:
            led_path = Path(temp_dir)
            device = self._new_device(led_path)
            writes = []
            write_attr = device._write_attr

            def record_write(attr, value):
                writes.append(attr)
                return write_attr(attr, value)

            device._write_attr = record_write

            cases = (
                (RGBMode.Rainbow, "chroma", 25, "low", "33"),
                (RGBMode.Spiral, "rainbow", 0, "high", "100"),
            )
            for mode, effect, brightness, speed, expected_speed in cases:
                with self.subTest(mode=mode):
                    device.set_color(
                        mode=mode,
                        color=Color(255, 0, 0),
                        brightness=brightness,
                        speed=speed,
                    )
                    self.assertEqual((led_path / "profile").read_text(), "3")
                    self.assertEqual((led_path / "mode").read_text(), "custom")
                    self.assertEqual((led_path / "effect").read_text(), effect)
                    self.assertEqual(
                        (led_path / "brightness").read_text(), str(brightness)
                    )
                    self.assertEqual(
                        (led_path / "speed").read_text(), expected_speed
                    )
                    self.assertEqual((led_path / "enabled").read_text(), "true")

            self.assertEqual(
                writes[:7],
                [
                    "profile",
                    "mode",
                    "speed",
                    "multi_intensity",
                    "brightness",
                    "effect",
                    "enabled",
                ],
            )
            capabilities = device.get_mode_capabilities()
            self.assertTrue(capabilities[RGBMode.Rainbow].brightness)
            self.assertTrue(capabilities[RGBMode.Spiral].brightness)

    def test_brightness_scales_to_device_range(self):
        with TemporaryDirectory() as temp_dir:
            led_path = Path(temp_dir)
            device = self._new_device(led_path)
            (led_path / "max_brightness").write_text("200\n")
            device._max_brightness_val = None

            device.set_color(
                mode=RGBMode.Rainbow,
                color=Color(255, 0, 0),
                brightness=25,
            )

            self.assertEqual((led_path / "brightness").read_text(), "50")

    def test_rgb_values_scale_to_multi_intensity_range(self):
        with TemporaryDirectory() as temp_dir:
            led_path = Path(temp_dir)
            device = self._new_device(led_path)

            device.set_color(
                mode=RGBMode.Solid,
                color=Color(255, 128, 0),
                brightness=50,
            )

            self.assertEqual(
                (led_path / "multi_intensity").read_text(), "100 50 0"
            )

    def test_capabilities_follow_effect_index(self):
        with TemporaryDirectory() as temp_dir:
            led_path = Path(temp_dir)
            device = self._new_device(led_path)
            (led_path / "effect_index").write_text("monocolor breathe\n")

            capabilities = device.get_mode_capabilities()

            self.assertFalse(capabilities[RGBMode.Rainbow].brightness)
            self.assertNotIn(RGBMode.Spiral, capabilities)
            self.assertNotIn(RGBMode.Rainbow, device.hardware_supported_modes)
            self.assertNotIn(RGBMode.Spiral, device.hardware_supported_modes)

    def test_reapplying_native_effect_restores_external_changes(self):
        with TemporaryDirectory() as temp_dir:
            led_path = Path(temp_dir)
            device = self._new_device(led_path)

            device.set_color(
                mode=RGBMode.Rainbow,
                color=Color(255, 0, 0),
                brightness=25,
                speed="low",
            )
            (led_path / "effect").write_text("monocolor")
            (led_path / "brightness").write_text("100")

            device.set_color(
                mode=RGBMode.Rainbow,
                color=Color(255, 0, 0),
                brightness=25,
                speed="low",
            )

            self.assertEqual((led_path / "effect").read_text(), "chroma")
            self.assertEqual((led_path / "brightness").read_text(), "25")


if __name__ == "__main__":
    unittest.main()
