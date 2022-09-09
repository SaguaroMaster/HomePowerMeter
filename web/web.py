#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import threading
import pandas

from flask import Flask, render_template, send_from_directory, make_response, request
app = Flask(__name__)

import sqlite3
#conn=sqlite3.connect('./dummy.db', check_same_thread=False)
conn=sqlite3.connect('/home/pi/dummy.db', check_same_thread=False)
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

def getFirstData():
	for row in curs.execute("SELECT * FROM data ORDER BY timestamp ASC LIMIT 1"):
		time = str(row[0])
		power = row[1]
		energy = row[2]
	#conn.close()
	return time, power, energy


def getHistDataPower (numSamples1, numSamples2):
	curs.execute("SELECT * FROM data WHERE timestamp >= '" + str(numSamples1) + "' AND timestamp <= '" + str(numSamples2) + "' ORDER BY timestamp DESC")
	data = curs.fetchall()
	dates = []
	power = []
	for row in reversed(data):
		dates.append(row[0])
		power.append(row[1])
	return dates, power

def getHistDataEnergy (numSamples1, numSamples2):
	datesSum = []
	energySum = []
	timeInterval = pandas.date_range(str(numSamples1)[:10],str(numSamples2)[:10],freq='d').tolist()
	for entry1 in timeInterval[:len(timeInterval)-1]:
		entry2 = entry1 + timedelta(days=1)
		curs.execute("SELECT SUM(energy) FROM data WHERE timestamp >= '" + str(entry1) + "' AND timestamp <= '" + str(entry2) + "'")
		dataSum = curs.fetchall()
		datesSum.append(str(entry1))
		energySum.append(dataSum[0][0])
	return datesSum, energySum

def setGlobalVars():
	global numSamples1, numSamples2
	numSamples1, nada2, nada1 = getLastData()
	numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
	numSamples2 = numSamples1 + timedelta(days=1)

#initialize global variables
global numSamples1, numSamples2
setGlobalVars()

# main route 
@app.route("/")
def index():
	global  numSamples1, numSamples2

	setGlobalVars()

	numSamples2_1 = numSamples2 - timedelta(days=1)
	
	numSamples1_disp = str(numSamples1)[:10]
	numSamples2_disp = str(numSamples2_1)[:10]
	
	lastDate, power, energy = getLastData()
	firstDate, nada1, nada2 = getFirstData()

	templateData = {
      'power'		: power,
      'energy'		: energy,
	  'minDateSel'	: numSamples1_disp,
	  'maxDateSel'	: numSamples2_disp,
	  'minDate'		: firstDate[:10],
	  'maxDate'		: lastDate[:10],
	  'maxDateFull'	: lastDate,
	}

	return render_template('index_gage.html', **templateData)


@app.route('/', methods=['POST'])
def my_form_post():
    global  numSamples1, numSamples2

    numSamples1 = request.form['numSamples1']
    numSamples2 = request.form['numSamples2']
    
    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2)[:10]

    numSamples2 = str(datetime.strptime(numSamples2, "%Y-%m-%d") + timedelta(days=1))

    lastDate, power, energy = getLastData()
    firstDate, nada1, nada2 = getFirstData()

    templateData = {
      'power'		: power,
      'energy'		: energy,
	  'minDateSel'	: numSamples1_disp,
	  'maxDateSel'	: numSamples2_disp,
	  'minDate'		: firstDate[:10],
	  'maxDate'		: lastDate[:10],
	  'maxDateFull'	: lastDate,
	}

    return render_template('index_gage.html', **templateData)

@app.route('/<path:filename>', methods=['GET', 'POST'])
def download(filename):
	return send_from_directory("/home/pi", filename)

@app.route('/plot/power')
def plot_power():
	try:
		lock.acquire(True)
		times, power = getHistDataPower(numSamples1, numSamples2)
		for j in range(len(times)):
			times[j]=times[j][5:19]
		xs = times
		ys = power
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Power [kW]")
		axis.set_xlabel("Date[M:D H:M:S]")
		axis.set_xticks([0, int(len(ys)/2), int(len(ys)/1.1)])
		axis.grid(True)
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
			times[j]=times[j][5:10]
		xs = times
		ys = energy
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Energy / day [kWh]")
		axis.set_xlabel("Date[Month : Day")
		axis.set_xticks([0, int(len(ys)/2), int(len(ys)/1.1)])
		axis.grid(True)
		axis.bar(xs, ys, width=0.5)
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
