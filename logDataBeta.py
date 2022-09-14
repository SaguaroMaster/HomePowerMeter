#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import random
from threading import Timer

dbname='/home/pi/dummy.db'
sampleFreqency = 60 #seconds
flashCount = 0
time1 = time.time()

# log sensor data on database
def logData (power, energy):
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	
	curs.execute("INSERT INTO data values(datetime('now'), (?), (?))", (power, energy))
	conn.commit()
	conn.close()

def doStuff():
	energy = random.randint(1,10)
	power = energy * 0.36/(sampleFreqency/10) # kW
	print("Power: " + str(power) + "kW, Energy: " + str(energy) + "Wh")
	#logData(power, energy)

	flashCount = 0

	time1 = time.time()
	t = Timer(2.0, doStuff)
	t.start()
# main function
t = Timer(2.0, doStuff)
t.start()