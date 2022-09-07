#!/usr/bin/env python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  


def flashCounter(self):
    if(GPIO.input==True):
        print("Flash Detected!")

GPIO.add_event_detect(17, GPIO.RISING, callback=flashCounter, bouncetime=100)

while True:
    pass