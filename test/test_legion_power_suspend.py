"""Power-state regressions without invoking any real EC or ACPI backend."""
import importlib.util
import logging
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class LegionPowerSuspendTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock(name='fake-backend')
        self.state = True
        self.fail_restore = False
        self.backend.get_power_led.side_effect = lambda: self.state
        def set_led(enabled):
            if enabled and self.fail_restore:
                return False
            self.state = enabled
            return True
        self.backend.set_power_led.side_effect = set_led
        config = types.ModuleType('config')
        config.logger = logging.getLogger('legion-suspend-test')
        backend_module = types.ModuleType('power_led_backend')
        backend_module.select_backend = lambda **kwargs: self.backend
        path = Path(__file__).resolve().parents[1] / 'py_modules/devices/legion_power_led_mixin.py'
        spec = importlib.util.spec_from_file_location('isolated_power_mixin', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'config': config, 'power_led_backend': backend_module}):
            spec.loader.exec_module(module)
        class Device(module.LegionPowerLEDMixin):
            POWER_LED_OFFSET = 0x52
            POWER_LED_BIT = 5
        self.device = Device()
        self.settings = {'power_led_suspend_off': True}

    def test_duplicate_suspend_preserves_original_on_state(self):
        self.device.suspend(self.settings)
        self.device.suspend(self.settings)
        self.assertFalse(self.state)
        self.device.resume()
        self.assertTrue(self.state)
        self.assertIsNone(self.device._power_led_state)
        self.assertEqual(self.backend.get_power_led.call_count, 1)

    def test_originally_off_stays_off_and_next_cycle_takes_new_snapshot(self):
        self.state = False
        self.device.suspend(self.settings)
        self.device.resume()
        self.assertFalse(self.state)
        self.assertIsNone(self.device._power_led_state)
        self.state = True
        self.device.suspend(self.settings)
        self.device.resume()
        self.assertTrue(self.state)

    def test_failed_restore_can_retry(self):
        self.device.suspend(self.settings)
        self.fail_restore = True
        self.device.resume()
        self.assertTrue(self.device._power_led_state)
        self.assertFalse(self.state)
        self.fail_restore = False
        self.device.resume()
        self.assertTrue(self.state)
        self.assertIsNone(self.device._power_led_state)

    def test_disabled_setting_does_not_touch_hardware(self):
        self.device.suspend({'power_led_suspend_off': False})
        self.device.resume()
        self.backend.set_power_led.assert_not_called()

    def test_unknown_state_does_not_force_led_on(self):
        self.state = None
        self.device.suspend(self.settings)
        self.device.resume()
        self.backend.set_power_led.assert_not_called()

    def test_duplicate_resume_does_not_write_again(self):
        self.device.suspend(self.settings)
        self.device.resume()
        self.device.resume()
        self.assertEqual(self.backend.set_power_led.call_count, 2)
