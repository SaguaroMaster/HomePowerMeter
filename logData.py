#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import random
import threading

dbname='dummy.db'
sampleFreqency = 10
reset = True
time1 = time.time()

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


