#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gpiozero import Button as btn

button = btn(17)
button.when_pressed = print("Flash!")


while True:
    pass