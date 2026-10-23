import logging
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py_modules"))

# Keep the tests independent from Decky, HID, EC and the real /sys tree.
config = types.ModuleType("config")
config.DEFAULT_BRIGHTNESS = 100
config.LED_PATH = "/nonexistent"
config.SOFTWARE_EFFECT_UPDATE_RATE = 30.0
config.logger = logging.getLogger("huesync-test")
sys.modules["config"] = config

from devices.onexplayer3 import OneXPlayer3LEDDevice
from utils import Color, RGBMode


PRIMARY = "go:rgb:joystick_rings"
SECONDARY = "oxp:rgb:guide_button"
REAR = "oxp:rgb:rear_logo"
ZONE_NAMES = (PRIMARY, SECONDARY, REAR)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
ZONE_COLORS = {"secondary": GREEN, "rear": BLUE}
ALL_ENABLED = {"primary": True, "secondary": True, "rear": True}


def build_led_root(
    root: Path,
    names: tuple[str, ...] = ZONE_NAMES,
    primary_effects: str = "monocolor breathing warm_sun",
) -> Path:
    """Create a temporary sysfs tree shaped like the hid-oxp driver."""
    for name in names:
        node = root / name
        node.mkdir()
        (node / "brightness").write_text("100\n")
        (node / "max_brightness").write_text("100\n")
        (node / "multi_intensity").write_text("0 0 0\n")
        (node / "multi_index").write_text("red green blue\n")
        (node / "multi_max_intensity").write_text("255 255 255\n")
        (node / "effect").write_text("monocolor\n")
        effects = primary_effects if name == PRIMARY else "monocolor breathing"
        (node / "effect_index").write_text(effects + "\n")
        if name == PRIMARY:
            (node / "enabled").write_text("true\n")
            (node / "speed").write_text("5\n")
            (node / "speed_range").write_text("0 9\n")
    return root


class OneXPlayer3SysfsTests(unittest.TestCase):
    def setUp(self):
        self._temp = TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.devices = []

    def tearDown(self):
        for device in self.devices:
            try:
                device.stop_effects()
            except Exception:
                pass
        self._temp.cleanup()

    def _device(self, names=ZONE_NAMES, primary_effects="monocolor breathing warm_sun"):
        build_led_root(self.root, names=names, primary_effects=primary_effects)
        device = OneXPlayer3LEDDevice(led_root=str(self.root))
        self.devices.append(device)
        return device

    def _attr(self, zone: str, attribute: str) -> str:
        return (self.root / zone / attribute).read_text().strip()

    def _colors(self) -> dict[str, str]:
        paths = {"primary": PRIMARY, "secondary": SECONDARY, "rear": REAR}
        return {
            zone: self._attr(node, "multi_intensity")
            for zone, node in paths.items()
        }

    def _assert_colors(self, expected: dict[str, str]):
        actual = self._colors()
        for zone, color in expected.items():
            with self.subTest(zone=zone):
                self.assertEqual(actual[zone], color)

    def test_advertises_three_zone_names_and_primary_enable(self):
        device = self._device()

        self.assertTrue(OneXPlayer3LEDDevice.is_available(led_root=str(self.root)))
        self.assertFalse(
            OneXPlayer3LEDDevice.is_available(led_root=str(self.root / "missing"))
        )

        zones = {zone["id"]: zone for zone in device.get_device_capabilities()["zones"]}
        self.assertEqual(set(zones), {"primary", "secondary", "rear"})
        for zone in zones.values():
            self.assertTrue(zone.get("name_key"))
        self.assertIs(zones["primary"].get("enabled_control"), True)

    def test_solid_writes_independent_zone_colors_at_full_brightness(self):
        device = self._device()

        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )

        self._assert_colors(
            {"primary": "255 0 0", "secondary": "0 255 0", "rear": "0 0 255"}
        )
        for zone in ZONE_NAMES:
            with self.subTest(zone=zone):
                self.assertEqual(self._attr(zone, "brightness"), "100")

    def test_each_zone_toggles_without_affecting_the_others(self):
        device = self._device()
        lit = {"primary": "255 0 0", "secondary": "0 255 0", "rear": "0 0 255"}

        for target in ("primary", "secondary", "rear"):
            with self.subTest(target=target):
                device.set_color(
                    mode=RGBMode.Solid,
                    color=RED,
                    zone_colors=ZONE_COLORS,
                    zone_enabled=ALL_ENABLED,
                )
                device.set_color(
                    mode=RGBMode.Solid,
                    color=RED,
                    zone_colors=ZONE_COLORS,
                    zone_enabled={
                        "primary": target != "primary",
                        "secondary": target != "secondary",
                        "rear": target != "rear",
                    },
                )
                expected = dict(lit)
                expected[target] = "0 0 0"
                self._assert_colors(expected)

    def test_global_disable_zeros_every_zone(self):
        device = self._device()
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )

        device.set_color(mode=RGBMode.Disabled, color=Color(0, 0, 0))

        self._assert_colors({"primary": "0 0 0", "secondary": "0 0 0", "rear": "0 0 0"})

    def test_global_disable_preserves_individual_zone_selection(self):
        device = self._device()
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled={"primary": True, "secondary": False, "rear": True},
        )
        self._assert_colors(
            {"primary": "255 0 0", "secondary": "0 0 0", "rear": "0 0 255"}
        )

        device.set_color(mode=RGBMode.Disabled, color=Color(0, 0, 0))
        self._assert_colors(
            {"primary": "0 0 0", "secondary": "0 0 0", "rear": "0 0 0"}
        )

        # Global disable only blacks out outputs; the independent choices for
        # primary (on), secondary (off) and rear (on) must survive.
        device.set_color(mode=RGBMode.Solid, color=RED)

        self._assert_colors(
            {"primary": "255 0 0", "secondary": "0 0 0", "rear": "0 0 255"}
        )

    def test_prescaled_color_is_not_darkened_by_brightness_again(self):
        device = self._device()

        device.set_color(mode=RGBMode.Solid, color=Color(64, 0, 0), brightness=25)

        self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "64 0 0")
        self.assertEqual(self._attr(PRIMARY, "brightness"), "100")

    def test_disabled_primary_stays_off_during_software_frames(self):
        device = self._device()
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled={"primary": False, "secondary": True, "rear": True},
        )

        device._set_solid_color(RED)

        self._assert_colors(
            {"primary": "0 0 0", "secondary": "0 255 0", "rear": "0 0 255"}
        )

    def test_native_oxp_sun_maps_to_warm_sun_without_touching_aux(self):
        device = self._device()
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )
        self.assertIn(RGBMode.OXP_SUN, device.get_mode_capabilities())

        device.set_color(mode=RGBMode.OXP_SUN, color=RED)

        self.assertEqual(self._attr(PRIMARY, "effect"), "warm_sun")
        self._assert_colors({"secondary": "0 255 0", "rear": "0 0 255"})

    def test_active_native_preset_accepts_aux_color_changes(self):
        device = self._device()
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )
        device.set_color(mode=RGBMode.OXP_SUN, color=RED)
        self.assertEqual(self._attr(PRIMARY, "effect"), "warm_sun")
        self._assert_colors({"secondary": "0 255 0", "rear": "0 0 255"})

        updated = {"secondary": Color(255, 255, 0), "rear": Color(0, 255, 255)}
        device.set_color(mode=RGBMode.OXP_SUN, color=RED, zone_colors=updated)

        self.assertEqual(self._attr(PRIMARY, "effect"), "warm_sun")
        self._assert_colors({"secondary": "255 255 0", "rear": "0 255 255"})

    def test_missing_native_effect_is_not_advertised(self):
        device = self._device(primary_effects="monocolor breathing")

        self.assertNotIn(RGBMode.OXP_SUN, device.get_mode_capabilities())
        self.assertNotIn(RGBMode.OXP_SUN, device.hardware_supported_modes)

    def test_missing_auxiliary_zone_is_omitted(self):
        device = self._device(names=(PRIMARY,))

        zones = [zone["id"] for zone in device.get_device_capabilities()["zones"]]
        self.assertEqual(zones, ["primary"])

        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )
        self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "255 0 0")

    def test_write_failure_reaches_the_caller(self):
        device = self._device()
        broken = self.root / SECONDARY / "multi_intensity"
        broken.unlink()
        broken.mkdir()

        with self.assertRaises(OSError):
            device.set_color(
                mode=RGBMode.Solid,
                color=RED,
                zone_colors=ZONE_COLORS,
                zone_enabled=ALL_ENABLED,
            )

    def test_reapplying_solid_with_init_restores_firmware_mutated_primary(self):
        device = self._device()

        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )

        # The firmware can reset the ring behind our back while control is idle;
        # the next init=True apply must rewrite every primary attribute instead of
        # trusting the cached values.
        (self.root / PRIMARY / "effect").write_text("warm_sun\n")
        (self.root / PRIMARY / "brightness").write_text("0\n")
        (self.root / PRIMARY / "enabled").write_text("false\n")

        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
            init=True,
        )

        self.assertEqual(self._attr(PRIMARY, "effect"), "monocolor")
        self.assertEqual(self._attr(PRIMARY, "brightness"), "100")
        self.assertEqual(self._attr(PRIMARY, "enabled"), "true")
        self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "255 0 0")

    def test_native_brightness_change_survives_driver_delayed_reset(self):
        # The hid-oxp driver queues work after every primary brightness or RGB
        # write that forces effect=monocolor and speed=5 (upstream PR #13,
        # oxp_gen_3_rgb_queue).  The queue drains ~50ms later, so a native
        # preset applied around a brightness change must write the brightness
        # first and re-apply the desired effect/speed afterwards, with the
        # cached values (which still describe the pre-reset state) invalidated.
        device = self._device()
        device.set_color(
            mode=RGBMode.Solid,
            color=RED,
            zone_colors=ZONE_COLORS,
            zone_enabled=ALL_ENABLED,
        )

        pending_reset = {"pending": False}
        original_write = device._write_attr

        def write_attr(zone, attr, value):
            original_write(zone, attr, value)
            # ``zone`` is the HueSync zone id ("primary"), not the sysfs dir.
            if zone == "primary" and attr == "brightness":
                pending_reset["pending"] = True

        def drain_delayed_queue():
            """Simulate the driver's delayed monocolor/speed-5 reset."""
            if not pending_reset["pending"]:
                return
            pending_reset["pending"] = False
            (self.root / PRIMARY / "effect").write_text("monocolor\n")
            (self.root / PRIMARY / "speed").write_text("5\n")

        def fake_sleep(_seconds):
            drain_delayed_queue()

        with mock.patch.object(device, "_write_attr", side_effect=write_attr):
            with mock.patch("time.sleep", side_effect=fake_sleep):
                device.set_color(
                    mode=RGBMode.OXP_SUN,
                    color=RED,
                    brightness_level="low",
                    speed="high",
                )
                # Any queued work the device code did not wait for still lands.
                drain_delayed_queue()

                self.assertEqual(self._attr(PRIMARY, "effect"), "warm_sun")
                self.assertEqual(self._attr(PRIMARY, "speed"), "9")
                self.assertEqual(self._attr(PRIMARY, "brightness"), "33")

                device.set_color(
                    mode=RGBMode.OXP_SUN,
                    color=RED,
                    brightness_level="medium",
                    speed="high",
                )
                drain_delayed_queue()

                # The second call changes only the brightness: the cached
                # effect/speed must not suppress re-applying them after the
                # delayed reset.
                self.assertEqual(self._attr(PRIMARY, "effect"), "warm_sun")
                self.assertEqual(self._attr(PRIMARY, "speed"), "9")
                self.assertEqual(self._attr(PRIMARY, "brightness"), "66")


if __name__ == "__main__":
    unittest.main()
