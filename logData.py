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
'''
import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
GPIO.add_event_detect(17, GPIO.RISING, callback=flashCounter, bouncetime=100) '''


def flashCounter():
	global flashCount
	'''if GPIO.input(17) > 0.5:
		flashCount = flashCount + 1'''
	flashCount = flashCount + 1

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
		flashCount = random.randint(3, 11)
		energy = flashCount #Wh
		power = energy * 0.36 # kW
		print("Power: " + str(power) + "kW, Energy: " + str(energy) + "Wh")
		logData(power, energy)
		time1 = time.time()


