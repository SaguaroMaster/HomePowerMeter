#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import threading

from flask import Flask, render_template, send_file, make_response, request
app = Flask(__name__)

import sqlite3
conn=sqlite3.connect('./dummy.db', check_same_thread=False)
curs=conn.cursor()

lock = threading.Lock()

# Retrieve LAST data from database
def getLastData():
	for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
		time = str(row[0])
		power = row[1]
		energy = row[2]
	#conn.close()
	return time, power, energy


def getHistData (numSamples1, numSamples2):
	curs.execute("SELECT * FROM data WHERE timestamp >= '" + str(numSamples1) + "' AND timestamp <= '" + str(numSamples2) + "' ORDER BY timestamp DESC")
	data = curs.fetchall()
	dates = []
	power = []
	energy = []
	for row in reversed(data):
		dates.append(row[0])
		power.append(row[1])
		energy.append(row[2])
	return dates, power, energy

def getHistDataEnergy (numSamples1, numSamples2):

	curs.execute("SELECT * FROM data WHERE timestamp >= '" + str(numSamples1) + "' AND timestamp <= '" + str(numSamples2) + "' ORDER BY timestamp DESC")
	data = curs.fetchall()

	dates = []
	energy = []
	
	for row in reversed(data):
		dates.append(row[0])
		energy.append(row[2])
	return dates, energy

def maxRowsTable():
	for row in curs.execute("select COUNT(power) from  data"):
		maxNumberRows=row[0]
	return maxNumberRows

#initialize global variables
global numSamples
numSamples = maxRowsTable()
if (numSamples > 101):
	numSamples = 100
global numSamples1, numSamples2
numSamples2, nada2, nada1 = getLastData()
numSamples1 = datetime.strptime(numSamples2, "%Y-%m-%d %H:%M:%S") - timedelta(days=1)


# main route 
@app.route("/")
def index():
	
	time, power, energy = getLastData()
	templateData = {
	  'time'		: time,
      'power'		: power,
      'energy'		: energy,
      'numSamples'	: numSamples
	}
	return render_template('index_gage.html', **templateData)


@app.route('/', methods=['POST'])
def my_form_post():
    global numSamples, numSamples1, numSamples2
    numSamples1 = request.form['numSamples1']
    numMaxSamples = maxRowsTable()
    if (numSamples > numMaxSamples):
        numSamples = (numMaxSamples-1)
    numSamples2 = request.form['numSamples2']
    time, power, energy = getLastData()
    
    templateData = {
	  'time'		: time,
      'power'		: power,
      'energy'		: energy,
      'numSamples'	: numSamples
	}
    return render_template('index_gage.html', **templateData)
	
	
@app.route('/plot/power')
def plot_power():
	try:
		lock.acquire(True)
		times, power, energy = getHistData(numSamples1, numSamples2)
		for j in range(len(times)):
			times[j]=times[j][5:19]
		ys = power
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Power [kW]")
		axis.set_xlabel("Date[M:D H:M:S]")
		axis.set_xticks(range(0, numSamples, int(numSamples/3)))
		axis.grid(True)
		xs = times
		axis.plot(xs, ys)
		canvas = FigureCanvas(fig)
		output = io.BytesIO()
		canvas.print_png(output)
		response = make_response(output.getvalue())
		response.mimetype = 'image/png'
		return response
	finally:
		lock.release()

@app.route('/plot/energy')
def plot_energy():
	try:
		lock.acquire(True)
		times, energy = getHistDataEnergy(numSamples1, numSamples2)
		for j in range(len(times)):
			times[j]=times[j][5:19]
		ys = energy
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Energy [Wh]")
		axis.set_xlabel("Date[M:D H:M:S]")
		axis.set_xticks([0, len(times)/5, len(times)/4, len(times)/3, len(times)/2, len(times)])
		axis.grid(True)
		xs = times
		axis.plot(xs, ys)
		canvas = FigureCanvas(fig)
		output = io.BytesIO()
		canvas.print_png(output)
		response = make_response(output.getvalue())
		response.mimetype = 'image/png'
		return response
	finally:
		lock.release()

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=False)