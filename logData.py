#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import random

dbname='dummy.db'
sampleFreqency = 10
flashCount = 0
reset = True
time1 = time.time()

import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  



def flashCounter(self):
	global flashCount
	if not GPIO.input(17):
		print("Button pressed!")
		flashCount = flashCount + 1
	else:
		print("Button released!")

GPIO.add_event_detect(17, GPIO.BOTH, callback=flashCounter, bouncetime=50)
# log sensor data on database
def logData (power, energy):
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	
	curs.execute("INSERT INTO data values(datetime('now'), (?), (?))", (power, energy))
	conn.commit()
	conn.close()

# main function
while True:
	if time.time() > time1+sampleFreqency:
		#flashCount = random.randint(3, 11)
		energy = flashCount #Wh
		power = energy * 0.36 # kW
		print("Power: " + str(power) + "kW, Energy: " + str(energy) + "Wh")
		#logData(power, energy)

		flashCount = 0

		time1 = time.time()


