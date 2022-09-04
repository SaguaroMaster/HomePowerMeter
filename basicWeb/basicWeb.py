#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request
app = Flask(__name__)

import sqlite3

# Retrieve data from database
def getData():
	conn=sqlite3.connect('./dummy.db')
	curs=conn.cursor()

	for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
		time = str(row[0])
		power = row[1]

	for row in curs.execute("SELECT SUM(energy) FROM data where timestamp >= datetime('now','-1 hours')"):
		energy = row[0]
		
	conn.close()
	return time, power, energy

# main route 
@app.route("/")
def index():
	
	time, power, energy = getData()
	templateData = {
	  'time'	: time,
      'power'	: power,
      'energy'	: energy
	}
	return render_template('index.html', **templateData)


if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=False)

