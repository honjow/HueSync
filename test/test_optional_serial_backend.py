"""Run import regressions in a fresh process, without Decky or hardware access."""
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OptionalSerialBackendTests(unittest.TestCase):
    def test_non_serial_devices_do_not_import_pyserial(self):
        script = r'''
import builtins
import logging
import sys
import types
from unittest.mock import Mock, patch
sys.path.insert(0, 'py_modules')
config = types.ModuleType('config')
for name, value in dict(PRODUCT_NAME='ONEXPLAYER X1 mini', SYS_VENDOR='AYANEO',
    DEFAULT_BRIGHTNESS=100, SOFTWARE_EFFECT_UPDATE_RATE=30.0,
    LED_PATH='/nonexistent', LED_SUSPEND_MODE_PATH='/nonexistent',
    IS_ALLY_LED_SUPPORTED=False, IS_LED_SUPPORTED=False,
    USE_SYSFS_SUSPEND_MODE=False).items():
    setattr(config, name, value)
config.logger = logging.getLogger('optional-serial-test')
sys.modules['config'] = config
hid = types.ModuleType('lib_hid')
hid.Device = object
hid.enumerate = lambda: []
sys.modules['lib_hid'] = hid
original_import = builtins.__import__
serial_attempts = []
def guarded_import(name, *args, **kwargs):
    if name == 'serial' or name.startswith('serial.') or name == 'termios':
        serial_attempts.append(name)
        raise ModuleNotFoundError("No module named 'termios'", name='termios')
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
from devices.onexplayer import OneXLEDDevice
from devices.onexplayer3 import OneXPlayer3LEDDevice
from utils import Color
# Stub unrelated hardware constructors, not the OneX modules under test.
for module_name, class_name in [('asus', 'AsusLEDDevice'), ('asus_ally', 'AllyLEDDevice'),
    ('ayaneo', 'AyaNeoLEDDevice'), ('gpd', 'GPDLEDDevice'), ('msi', 'MSILEDDevice'),
    ('legion_go2', 'LegionGo2LEDDevice'), ('legion_go_s', 'LegionGoSLEDDevice'),
    ('legion_go_tablet', 'LegionGoTabletLEDDevice'), ('zotac', 'ZotacLEDDevice')]:
    module = types.ModuleType('devices.' + module_name)
    setattr(module, class_name, type(class_name, (), {}))
    sys.modules[module.__name__] = module
from huesync import LedControl
assert LedControl().device.__class__.__name__ == 'AyaNeoLEDDevice'
with patch('huesync.SYS_VENDOR', 'ONE-NETBOOK'), patch('huesync.PRODUCT_NAME', 'ONEXPLAYER 3'), \
     patch.object(OneXPlayer3LEDDevice, 'is_available', return_value=True), \
     patch.object(OneXPlayer3LEDDevice, '__init__', return_value=None):
    assert isinstance(LedControl().device, OneXPlayer3LEDDevice)
device = OneXLEDDevice()
transport = Mock()
transport.is_ready.return_value = True
transport.set_led_color_new.return_value = True
with patch('devices.onexplayer.OneXLEDDeviceHID', return_value=transport):
    device._set_hardware_color(color=Color(255, 0, 0))
    assert transport.set_led_color_new.called
assert serial_attempts == [], serial_attempts
# Missing dependency is isolated to the serial operation and logged.
with patch('devices.onexplayer.logger') as logger:
    device.set_onex_color_serial(Color(255, 0, 0))
    assert logger.error.called
assert serial_attempts == ['serial'], serial_attempts
# With a working serial backend, the existing operation still executes.
backend = types.ModuleType('led.onex_led_device_serial')
backend.OneXLEDDeviceSerial = Mock()
with patch.dict(sys.modules, {'led.onex_led_device_serial': backend}):
    device.set_onex_color_serial(Color(255, 0, 0))
    assert backend.OneXLEDDeviceSerial.return_value.set_led_color.called
'''
        result = subprocess.run([sys.executable, '-c', textwrap.dedent(script)],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
