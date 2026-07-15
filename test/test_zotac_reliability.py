import logging
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
PY_MODULES = ROOT / "py_modules"
sys.path.insert(0, str(PY_MODULES))

# Keep the unit tests independent from Decky, HID, and host hardware. Reuse
# stubs installed by other test modules when unittest discovery imports them
# in the same interpreter.
config = sys.modules.get("config", types.ModuleType("config"))
config.DEFAULT_BRIGHTNESS = 100
config.LED_PATH = "/nonexistent"
config.PRODUCT_NAME = "TEST DEVICE"
config.SOFTWARE_EFFECT_UPDATE_RATE = 30.0
config.SYS_VENDOR = "TEST"
config.logger = logging.getLogger("huesync-zotac-test")
sys.modules["config"] = config

lib_hid = sys.modules.get("lib_hid", types.ModuleType("lib_hid"))
lib_hid.Device = object
lib_hid.enumerate = lambda: []
sys.modules["lib_hid"] = lib_hid

from devices.zotac import ZotacLEDDevice
from led.zotac_led_device_hid import (
    CMD_SAVE_CONFIG,
    COMMAND_POS,
    SETTING_POS,
    ZOTAC_COMMAND_INTERFACE,
    ZOTAC_PRODUCT_ID,
    ZOTAC_VENDOR_IDS,
    ZotacLEDDeviceHID,
    _has_supported_device,
    _select_device_info,
)
from utils import Color, RGBMode


class FakeZotacTransport:
    def __init__(self, ready=True, apply_error=None):
        self.ready = ready
        self.apply_error = apply_error
        self.closed = False
        self.calls = []

    def is_ready(self):
        return self.ready

    def close(self):
        self.closed = True

    def apply_effect(self, effect, color, speed, brightness, persist=True):
        self.calls.append(
            ("effect", effect, color, speed, brightness, persist)
        )
        if self.apply_error:
            raise self.apply_error

    def apply_disabled(self, persist=True):
        self.calls.append(("disabled", persist))
        if self.apply_error:
            raise self.apply_error


class ZotacInterfaceSelectionTests(unittest.TestCase):
    def test_only_selects_the_command_interface(self):
        vendor_id = ZOTAC_VENDOR_IDS[0]
        wrong_interface = {
            "vendor_id": vendor_id,
            "product_id": ZOTAC_PRODUCT_ID,
            "interface_number": 1,
            "path": b"wrong",
        }
        command_interface = {
            "vendor_id": vendor_id,
            "product_id": ZOTAC_PRODUCT_ID,
            "interface_number": ZOTAC_COMMAND_INTERFACE,
            "path": b"command",
        }

        self.assertIsNone(_select_device_info([wrong_interface]))
        self.assertIs(
            _select_device_info([wrong_interface, command_interface]),
            command_interface,
        )

    def test_detects_the_controller_before_interface_three_appears(self):
        partial_device = {
            "vendor_id": ZOTAC_VENDOR_IDS[0],
            "product_id": ZOTAC_PRODUCT_ID,
            "interface_number": 1,
        }

        self.assertTrue(_has_supported_device([partial_device]))
        self.assertIsNone(_select_device_info([partial_device]))

    def test_dmi_detection_does_not_depend_on_hid_enumeration(self):
        with (
            patch("devices.zotac.SYS_VENDOR", "ZOTAC"),
            patch("devices.zotac.PRODUCT_NAME", "ZOTAC GAMING ZONE"),
            patch.object(
                ZotacLEDDeviceHID,
                "has_supported_device",
                return_value=False,
            ),
        ):
            self.assertTrue(ZotacLEDDevice.should_use())


class ZotacRetryTests(unittest.TestCase):
    def setUp(self):
        for target in ("devices.zotac.logger", "devices.led_device.logger"):
            logger_patcher = patch(target)
            logger_patcher.start()
            self.addCleanup(logger_patcher.stop)

    def test_replays_the_full_transaction_after_reopening(self):
        first = FakeZotacTransport(apply_error=RuntimeError("timeout"))
        second = FakeZotacTransport()
        factory = Mock(side_effect=[first, second])
        device = ZotacLEDDevice()

        with (
            patch("devices.zotac.ZotacLEDDeviceHID", factory),
            patch("devices.zotac.time.sleep") as sleep,
        ):
            device.set_color(
                mode=RGBMode.Solid,
                color=Color(12, 34, 56),
                persist=False,
            )

        self.assertTrue(first.closed)
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(len(first.calls), 1)
        self.assertEqual(len(second.calls), 1)
        self.assertFalse(second.calls[0][-1])
        sleep.assert_called_once_with(0.5)

    def test_closes_not_ready_devices_and_propagates_final_failure(self):
        transports = [FakeZotacTransport(ready=False) for _ in range(4)]
        factory = Mock(side_effect=transports)
        device = ZotacLEDDevice()

        with (
            patch("devices.zotac.ZotacLEDDeviceHID", factory),
            patch("devices.zotac.time.sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "after 4 attempts"):
                device.set_color(
                    mode=RGBMode.Solid,
                    color=Color(12, 34, 56),
                )

        self.assertEqual(factory.call_count, 4)
        self.assertTrue(all(transport.closed for transport in transports))

class ZotacPersistenceTests(unittest.TestCase):
    def test_effect_can_be_applied_without_saving_firmware_config(self):
        device = ZotacLEDDeviceHID()
        device.set_uniform_color = Mock()
        device.set_effect = Mock()
        device.set_speed = Mock()
        device.set_brightness = Mock()
        device.save_config = Mock()

        device.apply_effect(4, Color(12, 34, 56), 1, 100, persist=False)

        device.set_uniform_color.assert_called_once()
        device.set_effect.assert_called_once_with(4)
        device.set_speed.assert_called_once_with(1)
        device.set_brightness.assert_called_once_with(100)
        device.save_config.assert_not_called()

    def test_default_effect_still_saves_firmware_config(self):
        device = ZotacLEDDeviceHID()
        device.set_uniform_color = Mock()
        device.set_effect = Mock()
        device.set_speed = Mock()
        device.set_brightness = Mock()
        device.save_config = Mock()

        device.apply_effect(4, Color(12, 34, 56), 1, 100)

        device.save_config.assert_called_once_with()

    def test_disabled_mode_obeys_the_persistence_policy(self):
        device = ZotacLEDDeviceHID()
        device.set_effect = Mock()
        device.save_config = Mock()

        device.apply_disabled(persist=False)

        device.set_effect.assert_called_once()
        device.save_config.assert_not_called()

    def test_save_config_rejects_a_nonzero_status(self):
        device = ZotacLEDDeviceHID()
        response = bytearray(64)
        response[COMMAND_POS] = CMD_SAVE_CONFIG
        response[SETTING_POS] = 1
        device._exchange = Mock(return_value=bytes(response))

        with self.assertRaisesRegex(RuntimeError, "save-config"):
            device.save_config()


if __name__ == "__main__":
    unittest.main()
