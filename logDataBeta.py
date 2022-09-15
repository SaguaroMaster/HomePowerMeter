#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import random
from threading import Timer

dbname='/home/pi/dummy.db'
sampleFreqency = 10 #seconds
flashCount = 0
time1 = time.time()
count = 0

import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  


def flashCounter(self):
	global flashCount, time1
	if not GPIO.input(17):
		print("Light!")
		flashCount = flashCount + 1
	if time.time() > time1+sampleFreqency:
		print(time.time)
		energy = flashCount #Wh
		power = energy * 0.36/(sampleFreqency/10) # kW
		print("Power: " + str(power) + "kW, Energy: " + str(energy) + "Wh")
		#logData(power, energy)
		flashCount = 0
		time1 = time.time()

GPIO.add_event_detect(17, GPIO.BOTH, callback=flashCounter, bouncetime=50)
# log sensor data on database
def logData (power, energy):
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	
	curs.execute("INSERT INTO data values(datetime('now'), (?), (?))", (power, energy))
	conn.commit()
	conn.close()

while True:
	time.sleep(0.1)