from typing import Literal


def buf(x):
    return bytes(x) + bytes(64 - len(x))


RgbMode = Literal["disabled", "solid", "pulse", "rainbow", "spiral", "duality", "oxp"]
