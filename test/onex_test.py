#!/bin/python3

import hid as hid

_vid=0x1A2C
_pid=0xB001

hid_device_list = hid.enumerate(_vid, _pid)

print(hid_device_list)

print(f"path={hid_device_list[0]['path'].decode('utf-8')}")