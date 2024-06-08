#!/bin/python3

import hid as hid

_vid=0x0B05
_pid=0x1ABE

hid_device_list = hid.enumerate(_vid, _pid)

print(hid_device_list)

print(f"path={hid_device_list[0]['path'].decode('utf-8')}")