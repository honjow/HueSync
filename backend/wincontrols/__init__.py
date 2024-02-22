#!/usr/bin/env python3

__all__ = ['WinControls','defaults']

from .hardware import WinControls

defaults = """
du=W
dd=S
dl=A
dr=D

a=A
b=B
x=X
y=Y

lu=UP
ld=DOWN
ll=LEFT
lr=RIGHT

l1=MOUSE_LEFT
r1=MOUSE_RIGHT
l2=MOUSE_MIDDLE
r2=MOUSE_FAST
l3=SPACE
r3=ENTER

l41=NONE
l42=NONE
l43=NONE
l44=NONE

r41=NONE
r42=NONE
r43=NONE
r44=NONE

rumble=2
ledmode=solid
colour=65535

ldead=-8
lcent=-8
rdead=-8
rcent=-8

l4delay1=0
l4delay2=0
l4delay3=0
l4delay4=300

r4delay1=0
r4delay2=0
r4delay3=0
r4delay4=300
"""
