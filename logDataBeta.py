#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import random
import asyncio


dbname='/home/pi/dummy.db'
sampleFreqency = 3 #seconds
flashCount = 0
time1 = time2 = time3 = time.time()


# log sensor data on database
def logData (power, energy):
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	
	curs.execute("INSERT INTO data values(datetime('now'), (?), (?))", (power, energy))
	conn.commit()
	conn.close()

async def test():
	
	time2 = time.time
	energy = random.randint(1,10)
	#energy = flashCount #Wh
	power = energy * 0.36/(sampleFreqency/10) # kW
	print("Power: " + str(power) + "kW, Energy: " + str(energy) + "Wh")
	#logData(power, energy)

	flashCount = 0

	time1 = time.time()
	time3 = time.time()
	timeDiff = time3-time1
	print(timeDiff)
	await asyncio.sleep(3)
	return test()
# main function
test()
	


