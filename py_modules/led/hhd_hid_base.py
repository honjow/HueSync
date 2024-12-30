from typing import Literal


def buf(x):
    return bytes(x) + bytes(64 - len(x))


FEATURE_KBD_DRIVER = 0x5A
FEATURE_KBD_APP = 0x5D
FEATURE_KBD_ID = FEATURE_KBD_APP


def RGB_PKEY_INIT(key):
    return [
        buf(
            [
                key,
                0x41,
                0x53,
                0x55,
                0x53,
                0x20,
                0x54,
                0x65,
                0x63,
                0x68,
                0x2E,
                0x49,
                0x6E,
                0x63,
                0x2E,
            ]
        ),
    ]


RGB_APPLY = buf([FEATURE_KBD_ID, 0xB4])
RGB_SET = buf([FEATURE_KBD_ID, 0xB5])
RGB_INIT = RGB_PKEY_INIT(FEATURE_KBD_ID)


RgbMode = Literal["disabled", "solid", "pulse", "rainbow", "spiral", "duality", "oxp"]
