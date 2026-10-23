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
CURRENT_PRIMARY = "oxp:rgb:joystick_rings"
PRIMARY_NAMES = (CURRENT_PRIMARY, PRIMARY)
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
        effects = primary_effects if name in PRIMARY_NAMES else "monocolor breathing"
        (node / "effect_index").write_text(effects + "\n")
        if name in PRIMARY_NAMES:
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


    def test_both_primary_names_select_the_same_path_for_detection_and_writes(self):
        for primary in PRIMARY_NAMES:
            with self.subTest(primary=primary):
                root = self.root / primary.replace(":", "_")
                root.mkdir()
                build_led_root(root, names=(primary, SECONDARY, REAR))
                self.assertTrue(OneXPlayer3LEDDevice.is_available(str(root)))
                device = OneXPlayer3LEDDevice(led_root=str(root))
                self.devices.append(device)
                self.assertEqual(device._sysfs_led_path, str(root / primary))
                device.set_color(
                    mode=RGBMode.Solid, color=RED,
                    zone_colors=ZONE_COLORS, zone_enabled=ALL_ENABLED,
                )
                self.assertEqual(
                    (root / primary / "multi_intensity").read_text(), "255 0 0"
                )
                self.assertEqual(
                    (root / REAR / "multi_intensity").read_text(), "0 0 255"
                )

    def test_prefers_current_primary_and_falls_back_if_it_is_incomplete(self):
        build_led_root(self.root, names=PRIMARY_NAMES)
        current = OneXPlayer3LEDDevice(led_root=str(self.root))
        self.devices.append(current)
        current.set_color(mode=RGBMode.Solid, color=RED)
        self.assertEqual(current._sysfs_led_path, str(self.root / CURRENT_PRIMARY))
        self.assertEqual(self._attr(CURRENT_PRIMARY, "multi_intensity"), "255 0 0")
        self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "0 0 0")

        (self.root / CURRENT_PRIMARY / "multi_intensity").unlink()
        self.assertTrue(OneXPlayer3LEDDevice.is_available(str(self.root)))
        legacy = OneXPlayer3LEDDevice(led_root=str(self.root))
        self.devices.append(legacy)
        self.assertEqual(legacy._sysfs_led_path, str(self.root / PRIMARY))
        legacy.set_color(mode=RGBMode.Solid, color=GREEN)
        self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "0 255 0")

        (self.root / PRIMARY / "brightness").unlink()
        self.assertFalse(OneXPlayer3LEDDevice.is_available(str(self.root)))

    def test_30hz_frames_allow_every_delayed_driver_write_to_complete(self):
        device = self._device()
        now = [0.0]
        pending = [None]
        submitted = []
        applied = []
        original_write = device._write_attr

        def advance(target):
            if pending[0] is not None and pending[0][0] <= target:
                applied.append(pending[0][1])
                pending[0] = None
            now[0] = target

        def wait_for_interval(seconds):
            advance(now[0] + seconds)
            return False

        def write_attr(zone, attr, value):
            original_write(zone, attr, value)
            if zone == "primary" and attr == "multi_intensity":
                submitted.append((now[0], value))
                # Model mod_delayed_work: every write replaces the deadline,
                # not a simple queue that eventually submits every frame.
                pending[0] = (now[0] + 0.050, value)

        with mock.patch("devices.onexplayer3.time.monotonic", side_effect=lambda: now[0]):
            with mock.patch.object(device._software_stop, "wait", side_effect=wait_for_interval):
                with mock.patch.object(device, "_write_attr", side_effect=write_attr):
                    with mock.patch("devices.onexplayer3.time.sleep") as sleep:
                        for frame in range(30):
                            if frame:
                                advance(now[0] + 1 / 30)
                            device._set_solid_color(Color(frame, 0, 0))
                        advance(now[0] + 0.060)
                        sleep.assert_not_called()

        self.assertEqual(len(submitted), 30)
        self.assertEqual(applied, [value for _, value in submitted])
        self.assertEqual(applied[-1], "29 0 0")
        for previous, following in zip(submitted, submitted[1:]):
            self.assertGreaterEqual(following[0] - previous[0], 0.075 - 1e-9)

    def test_interrupted_frame_does_not_write_and_stop_signals_before_join(self):
        device = self._device()
        with mock.patch("devices.onexplayer3.time.monotonic", return_value=0.0):
            device._set_solid_color(RED)
            with mock.patch.object(device._software_stop, "wait", return_value=True) as wait:
                device._set_solid_color(GREEN)
                wait.assert_called_once()
        self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "255 0 0")

        effect = mock.Mock()
        effect.stop.side_effect = lambda: self.assertTrue(device._software_stop.is_set())
        device._current_effect = effect
        device.stop_effects()
        effect.stop.assert_called_once()
        self.assertIsNone(device._current_effect)
        self.assertFalse(device._software_stop.is_set())

    def test_disabled_and_solid_bypass_frame_wait_and_new_effect_resets_clock(self):
        device = self._device()
        with mock.patch("devices.onexplayer3.time.monotonic", return_value=0.0):
            device._set_solid_color(RED)
            with mock.patch.object(device._software_stop, "wait") as wait:
                device.set_color(mode=RGBMode.Disabled)
                self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "0 0 0")
                device.set_color(mode=RGBMode.Solid, color=GREEN)
                self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "0 255 0")
                wait.assert_not_called()

                # Keep the real BaseLEDDevice dispatch, replacing only the
                # effect's background thread with a deterministic first frame.
                with mock.patch("devices.led_device.PulseEffect") as effect_class:
                    effect = effect_class.return_value
                    effect.start.side_effect = lambda: device._set_solid_color(BLUE)
                    device.set_color(mode=RGBMode.Pulse, color=BLUE)
                    self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "0 0 255")
                    wait.assert_not_called()
                    device.set_color(mode=RGBMode.Disabled)
                    effect.stop.assert_called_once()
                    self.assertEqual(self._attr(PRIMARY, "multi_intensity"), "0 0 0")


if __name__ == "__main__":
    unittest.main()
