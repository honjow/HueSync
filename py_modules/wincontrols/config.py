import struct
from config import logging

class KeyCodes:
    """Keycode mapping for the GPD Win controls. This is the same as the standard usb hid keycodes, up to RIGHTMETA/0xe7. After that are custom codes for the mouse buttons and wheel."""
    code = {
        "NONE": 0x00,

        "A": 0x04,
        "B": 0x05,
        "C": 0x06,
        "D": 0x07,
        "E": 0x08,
        "F": 0x09,
        "G": 0x0a,
        "H": 0x0b,
        "I": 0x0c,
        "J": 0x0d,
        "K": 0x0e,
        "L": 0x0f,
        "M": 0x10,
        "N": 0x11,
        "O": 0x12,
        "P": 0x13,
        "Q": 0x14,
        "R": 0x15,
        "S": 0x16,
        "T": 0x17,
        "U": 0x18,
        "V": 0x19,
        "W": 0x1a,
        "X": 0x1b,
        "Y": 0x1c,
        "Z": 0x1d,

        "1": 0x1e,
        "2": 0x1f,
        "3": 0x20,
        "4": 0x21,
        "5": 0x22,
        "6": 0x23,
        "7": 0x24,
        "8": 0x25,
        "9": 0x26,
        "0": 0x27,

        "ENTER": 0x28,
        "ESC": 0x29,
        "BACKSPACE": 0x2a,
        "TAB": 0x2b,
        "SPACE": 0x2c,
        "MINUS": 0x2d,
        "EQUAL": 0x2e,
        "LEFTBRACE": 0x2f,
        "RIGHTBRACE": 0x30,
        "BACKSLASH": 0x31,
        "HASHTILDE": 0x32,
        "SEMICOLON": 0x33,
        "APOSTROPHE": 0x34,
        "GRAVE": 0x35,
        "COMMA": 0x36,
        "DOT": 0x37,
        "SLASH": 0x38,
        "CAPSLOCK": 0x39,

        "F1": 0x3a,
        "F2": 0x3b,
        "F3": 0x3c,
        "F4": 0x3d,
        "F5": 0x3e,
        "F6": 0x3f,
        "F7": 0x40,
        "F8": 0x41,
        "F9": 0x42,
        "F10": 0x43,
        "F11": 0x44,
        "F12": 0x45,

        "SYSRQ": 0x46,
        "SCROLLLOCK": 0x47,
        "PAUSE": 0x48,
        "INSERT": 0x49,
        "HOME": 0x4a,
        "PAGEUP": 0x4b,
        "DELETE": 0x4c,
        "END": 0x4d,
        "PAGEDOWN": 0x4e,
        "RIGHT": 0x4f,
        "LEFT": 0x50,
        "DOWN": 0x51,
        "UP": 0x52,

        "NUMLOCK": 0x53,
        "KPSLASH": 0x54,
        "KPASTERISK": 0x55,
        "KPMINUS": 0x56,
        "KPPLUS": 0x57,
        "KPENTER": 0x58,
        "KP1": 0x59,
        "KP2": 0x5a,
        "KP3": 0x5b,
        "KP4": 0x5c,
        "KP5": 0x5d,
        "KP6": 0x5e,
        "KP7": 0x5f,
        "KP8": 0x60,
        "KP9": 0x61,
        "KP0": 0x62,
        "KPDOT": 0x63,

        "102ND": 0x64,
        "COMPOSE": 0x65,
        "POWER": 0x66,
        "KPEQUAL": 0x67,

        "F13": 0x68,
        "F14": 0x69,
        "F15": 0x6a,
        "F16": 0x6b,
        "F17": 0x6c,
        "F18": 0x6d,
        "F19": 0x6e,
        "F20": 0x6f,
        "F21": 0x70,
        "F22": 0x71,
        "F23": 0x72,
        "F24": 0x73,

        "OPEN": 0x74,
        "HELP": 0x75,
        "PROPS": 0x76,
        "FRONT": 0x77,
        "STOP": 0x78,
        "AGAIN": 0x79,
        "UNDO": 0x7a,
        "CUT": 0x7b,
        "COPY": 0x7c,
        "PASTE": 0x7d,
        "FIND": 0x7e,
        "MUTE": 0x7f,
        "VOLUMEUP": 0x80,
        "VOLUMEDOWN": 0x81,

        "KPCOMMA": 0x85,

        "RO": 0x87,
        "KATAKANAHIRAGANA": 0x88,
        "YEN": 0x89,
        "HENKAN": 0x8a,
        "MUHENKAN": 0x8b,
        "KPJPCOMMA": 0x8c,

        "HANGEUL": 0x90,
        "HANJA": 0x91,
        "KATAKANA": 0x92,
        "HIRAGANA": 0x93,
        "ZENKAKUHANKAKU": 0x94,

        "KPLEFTPAREN": 0xb6,
        "KPRIGHTPAREN": 0xb7,

        "LEFTCTRL": 0xe0,
        "LEFTSHIFT": 0xe1,
        "LEFTALT": 0xe2,
        "LEFTMETA": 0xe3,

        "RIGHTCTRL": 0xe4,
        "RIGHTSHIFT": 0xe5,
        "RIGHTALT": 0xe6,
        "RIGHTMETA": 0xe7,

        "MOUSE_WHEELUP": 0xe8,
        "MOUSE_WHEELDOWN": 0xe9,
        "MOUSE_LEFT": 0xea,
        "MOUSE_RIGHT": 0xeb,
        "MOUSE_MIDDLE": 0xec,
        "MOUSE_FAST": 0xed,

        "DPAD_UP": 0xff01,
        "DPAD_DOWN": 0xff02,
        "DPAD_LEFT": 0xff03,
        "DPAD_RIGHT": 0xff04,

        "BTN_A": 0xff05,
        "BTN_B": 0xff06,
        "BTN_X": 0xff07,
        "BTN_Y": 0xff08,

        "LSTICK_UP": 0xff09,
        "LSTICK_DOWN": 0xff0a,
        "LSTICK_LEFT": 0xff0b,
        "LSTICK_RIGHT": 0xff0c,

        "L3": 0xff0d,
        "R3": 0xff0e,

        "START": 0xff0f,
        "SELECT": 0xff10,
        "MENU": 0xff11,

        "L1": 0xff12,
        "R1": 0xff13,
        "L2": 0xff14,
        "R2": 0xff15,

        "RSTICK_UP": 0xff16,
        "RSTICK_DOWN": 0xff17,
        "RSTICK_LEFT": 0xff18,
        "RSTICK_RIGHT": 0xff19,
    }

    key = {v:k for k,v in code.items()}

class Setting:
    """Base class for configuration settings."""
    def __init__(self, offset, name, description):
        self.offset = offset
        self.name = name
        self.description = description
        self._values = 0,

    # Single value getter and setter
    def set(self, value):
        if type(value) == str:
            value = int(value)
        self._values = value,

    def get(self):
        return self._values[0]

    def apply(self, config: bytearray):
        struct.pack_into(self._format, config, self.offset, *self._values)

    def decode(self, config: bytearray):
        self._values = struct.unpack_from(self._format, config, self.offset)

    def __repr__(self):
        return f"{self.name}={self.get()}"

    def help(self):
        return f"{self.description} : {self.__doc__}"

class Key(Setting):
    """A button or trigger. Must be a valid keycode."""
    _format = '<H'
    kc = KeyCodes()

    def set(self, key: str):
        key = key.upper()
        if key not in Key.kc.code:
            raise RuntimeError(f"Invalid key '{key}'. Must be one of {list(Key.kc.code.keys())}")
        super().set(Key.kc.code[key])

    def get(self):
        if super().get() not in Key.kc.key:
            hex_code = hex(super().get())
            logging.error(f"Invalid key code {hex_code}")
            raise RuntimeError(f"Invalid key code {hex_code}")
        return Key.kc.key[super().get()]

class Signed(Setting):
    """Signed offset for the deadzone and centering settings. Keep to the range -10 to 10."""
    _format = '<b'

class Millis(Setting):
    """A delay in milliseconds."""
    _format = '<H'

class Rumble(Setting):
    """The rumble mode. 0=off, 1=low, 2=high."""
    _format = '<B'

    def set(self, value):
        if value not in ('0','1','2'):
            raise RuntimeError("Rumble must be 0,1 or 2.")
        super().set(value)

class LedMode(Setting):
    """(Win4 only) The LED mode. One of off, solid, breathe or rotate."""
    _format = '<B'

    code = {'off':0, 'solid':0x01, 'breathe':0x11, 'rotate':0x21}
    mode = {v:k for k,v in code.items()}

    def set(self, mode):
        mode = mode.lower()
        if mode not in self.code:
            raise RuntimeError(f"Invalid mode '{mode}'. Must be 'off', 'solid', 'breathe' or 'rotate'.")
        self._values = (self.code[mode], )

    def get(self):
        code = self._values[0]
        return self.mode.get(code, 'off')

class Colour(Setting):
    """(Win4 only) The LED colour. Given as a hex string in the format RRGGBB."""
    _format = "<BBB"

    def set(self, value):
        if type(value) == str:
            value = int(value, 16)
        self._values = (value & 0xff, (value >> 8) & 0xff, (value >> 16) & 0xff)

    def get(self):
        return f"{self._values[2]:02x}{self._values[1]:02x}{self._values[0]:02x}"
