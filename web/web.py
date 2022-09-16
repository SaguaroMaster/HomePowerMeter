#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from genericpath import sameopenfile
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from platform import system as sys
from flask import Flask, render_template, send_from_directory, make_response, request

import io
import os
import threading
import pandas
import dateutil.relativedelta
import calendar
import sqlite3


app = Flask(__name__)


if sys() == 'Windows':
	conn=sqlite3.connect('./dummy.db', check_same_thread=False)
else:
	conn=sqlite3.connect('/home/pi/dummy.db', check_same_thread=False)
	from gpiozero import CPUTemperature
curs=conn.cursor()

lock = threading.Lock()

#######################
costPerKwh = 0.14 #EUR
#######################

def getLastData():
	for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
		time = row[0]
		power = row[1]
	return time, power

def getFirstData():
	for row in curs.execute("SELECT * FROM data ORDER BY timestamp ASC LIMIT 1"):
		time = str(row[0])
		power = row[1]
	#conn.close()
	return time, power

def getHistDataPower (numSamples1, numSamples2):
	curs.execute("SELECT * FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '" + str(numSamples2) + "' ORDER BY timestamp DESC")
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
	timeInterval = pandas.date_range(str(numSamples2 - timedelta(days=30))[:10],str(numSamples2)[:10],freq='d').tolist()
	for entry1 in timeInterval[:len(timeInterval)-1]:
		entry2 = entry1 + timedelta(days=1)
		curs.execute("SELECT SUM(energy) FROM data WHERE timestamp >= '" + str(entry1) + "' AND timestamp <= '" + str(entry2) + "'")
		dataSum = curs.fetchall()
		datesSum.append(str(entry1))
		energySum.append(dataSum[0][0])
	
	energySum = [0 if v is None else v for v in energySum]
	energySum = convertEnergyToKwh(energySum)
	return datesSum, energySum

def getHistDataEnergyToday():
	entry1 = datetime.today()
	entry2 = entry1 + timedelta(days = 1)
	curs.execute("SELECT SUM(energy) FROM data WHERE timestamp >= '" + str(entry1)[:10] + "' AND timestamp <= '" + str(entry2)[:10] + "'")
	dataSum = curs.fetchall()
	if dataSum[0][0] is None:
		energyToday = 0
	else:
		energyToday = dataSum[0][0]/1000

	return energyToday

def getHistDataEnergyDailyAvg (numSamples1, numSamples2):
	datesSum = []
	energySum = []

	timeInterval = pandas.date_range(str(numSamples2 - timedelta(days=365))[:10],str(numSamples2)[:10],freq='M').tolist()
	for entry1 in timeInterval[:len(timeInterval)]:
		entry2 = entry1 + dateutil.relativedelta.relativedelta(months=1)
		curs.execute("SELECT SUM(energy) FROM data WHERE timestamp >= '" + str(entry1) + "' AND timestamp <= '" + str(entry2) + "'")
		dataSum = curs.fetchall()
		daysInMonth = int(calendar.monthrange(entry2.year, entry2.month)[1])
		datesSum.append(str(entry2))
		energySum.append([0 if dataSum[0][0] is None else dataSum[0][0]][0]/daysInMonth)

	energySum = [0 if v is None else v for v in energySum]
	energySum = convertEnergyToKwh(energySum)
	return datesSum, energySum

def getHistDataEnergyMonthly (numSamples1, numSamples2):
	datesSum = []
	energySum = []
	timeInterval = pandas.date_range(str(numSamples2 - timedelta(days=365))[:10],str(numSamples2)[:10],freq='M').tolist()
	for entry1 in timeInterval[:len(timeInterval)]:
		entry2 = entry1 + dateutil.relativedelta.relativedelta(months=1)
		curs.execute("SELECT SUM(energy) FROM data WHERE timestamp >= '" + str(entry1) + "' AND timestamp <= '" + str(entry2) + "'")
		dataSum = curs.fetchall()
		datesSum.append(str(entry2))
		energySum.append(dataSum[0][0])
	energySum = [0 if v is None else v for v in energySum]
	energySum = convertEnergyToKwh(energySum)
	return datesSum, energySum

def convertEnergyToKwh(energy):
	energy = [v/1000 for v in energy]
	return energy

def setGlobalVars():
	global numSamples1, numSamples2
	numSamples1, nada2 = getLastData()
	numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
	numSamples2 = numSamples1 + timedelta(days=1)

def getTemplateData(selDate):
	PowerToday = getHistDataPower(numSamples1, numSamples2)
	for j in range(len(PowerToday[0])):
		PowerToday[0][j]=PowerToday[0][j][11:16]

	DailyEnergy = getHistDataEnergy(numSamples1, numSamples2)	# DailyEnergy[0] - date // DailyEnergy[1] - energy values in kWh
	for j in range(len(DailyEnergy[0])):
		DailyEnergy[0][j]=DailyEnergy[0][j][5:10]
	DailyEnergyCost = [x * costPerKwh for x in DailyEnergy[1]]

	AverageEnergyDaily = getHistDataEnergyDailyAvg(numSamples1, numSamples2)
	for j in range(len(AverageEnergyDaily[0])):
		AverageEnergyDaily[0][j]=AverageEnergyDaily[0][j][5:7]
	AverageEnergyDailyCost = [x * costPerKwh for x in AverageEnergyDaily[1]]

	MonthlyEnergyConsumed = getHistDataEnergyMonthly(numSamples1, numSamples2)
	for j in range(len(MonthlyEnergyConsumed[0])):
		MonthlyEnergyConsumed[0][j]=MonthlyEnergyConsumed[0][j][5:7]
	MonthlyEnergyConsumedCost = [x * costPerKwh for x in MonthlyEnergyConsumed[1]]

	return PowerToday, DailyEnergy, DailyEnergyCost, AverageEnergyDaily, AverageEnergyDailyCost, MonthlyEnergyConsumed, MonthlyEnergyConsumedCost

def getCPUTemp():
	if sys() == 'Windows':
		temp = 69.69
	else:
		temp = round(CPUTemperature().temperature, 1)
	return temp

def basicTemplate():
	global  numSamples1, numSamples2
	setGlobalVars()

	numSamples2_1 = numSamples2 - timedelta(days=1)
	
	numSamples1_disp = str(numSamples1)[:10]
	numSamples2_disp = str(numSamples2_1)[:10]
	
	lastDate, power = getLastData()
	firstDate, nada1 = getFirstData()
	power = round(power, 2)

	energyToday = getHistDataEnergyToday()

	templateData = {
		'power'						: power,
		'energytoday'				: energyToday,
		'minDateSel'				: numSamples1_disp,
		'maxDateSel'				: numSamples2_disp,
		'minDate'					: firstDate[:10],
		'maxDate'					: lastDate[:10],
		'maxDateFull'				: lastDate[11:],
		'sysTemp'					: getCPUTemp()
	}

	return templateData

def saveSettings(samplingPeriod, language):
	curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), (?), (?))", (samplingPeriod, language))
	conn.commit()

def getSettings():
	for row in curs.execute("SELECT * FROM settings ORDER BY timestamp DESC LIMIT 1"):
		lastEdit = row[0]
		samplingPeriod = row[1]
		language = row[2]
		return lastEdit, samplingPeriod, language
	return None, None, None
	

#initialize global variables
global numSamples1, numSamples2
setGlobalVars()







# main route 
@app.route("/")
def index():
	global  numSamples1, numSamples2
	setGlobalVars()

	PowerToday, DailyEnergy, DailyEnergyCost, AverageEnergyDaily, AverageEnergyDailyCost, MonthlyEnergyConsumed, MonthlyEnergyConsumedCost = getTemplateData(numSamples1)

	numSamples2_1 = numSamples2 - timedelta(days=1)
	
	numSamples1_disp = str(numSamples1)[:10]
	numSamples2_disp = str(numSamples2_1)[:10]
	
	lastDate, power = getLastData()
	firstDate, nada1 = getFirstData()
	power = round(power, 2)

	energyToday = getHistDataEnergyToday()

	templateData = {
		'power'						: power,
		'energytoday'				: energyToday,
		'minDateSel'				: numSamples1_disp,
		'maxDateSel'				: numSamples2_disp,
		'minDate'					: firstDate[:10],
		'maxDate'					: lastDate[:10],
		'maxDateFull'				: lastDate[11:],
		'powerX'					: PowerToday[0],
		'powerY'					: PowerToday[1],
		'energyDailyMonthX'			: DailyEnergy[0],
		'energyDailyMonthY'			: DailyEnergy[1],
		'energyDailyMonthCostY'		: DailyEnergyCost,
		'averageEnergyX'			: AverageEnergyDaily[0],
		'averageEnergyY'			: AverageEnergyDaily[1],
		'averageEnergyCostY'		: AverageEnergyDailyCost,
		'totalEnergyX'				: MonthlyEnergyConsumed[0],
		'totalEnergyY'				: MonthlyEnergyConsumed[1],
		'totalEnergyCostY'			: MonthlyEnergyConsumedCost,
		'sysTemp'					: getCPUTemp()
	}

	return render_template('dashboard.html', **templateData)


@app.route('/', methods=['POST'])
def my_form_post():
    global  numSamples1, numSamples2

    numSamples2 = request.form['numSamples2']
    numSamples2 = datetime.strptime(numSamples2, "%Y-%m-%d")

    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2)[:10]

    numSamples2 = numSamples2 + timedelta(days=1)

    PowerToday, DailyEnergy, DailyEnergyCost, AverageEnergyDaily, AverageEnergyDailyCost, MonthlyEnergyConsumed, MonthlyEnergyConsumedCost = getTemplateData(numSamples1)

    lastDate, power = getLastData()
    firstDate, nada1 = getFirstData()
    power = round(power, 2)

    energyToday = getHistDataEnergyToday()

    templateData = {
		'power'						: power,
		'energytoday'				: energyToday,
		'minDateSel'				: numSamples1_disp,
		'maxDateSel'				: numSamples2_disp,
		'minDate'					: firstDate[:10],
		'maxDate'					: lastDate[:10],
		'maxDateFull'				: lastDate[11:],
		'powerX'					: PowerToday[0],
		'powerY'					: PowerToday[1],
		'energyDailyMonthX'			: DailyEnergy[0],
		'energyDailyMonthY'			: DailyEnergy[1],
		'energyDailyMonthCostY'		: DailyEnergyCost,
		'averageEnergyX'			: AverageEnergyDaily[0],
		'averageEnergyY'			: AverageEnergyDaily[1],
		'averageEnergyCostY'		: AverageEnergyDailyCost,
		'totalEnergyX'				: MonthlyEnergyConsumed[0],
		'totalEnergyY'				: MonthlyEnergyConsumed[1],
		'totalEnergyCostY'			: MonthlyEnergyConsumedCost,
		'sysTemp'					: getCPUTemp()
	}

    return render_template('dashboard.html', **templateData)

@app.route("/matplotlib_downloadable.html")
def old_graphs():
	templateData = basicTemplate()
	return render_template('matplotlib_downloadable.html', **templateData)

@app.route("/matplotlib_downloadable.html", methods=['POST'])
def old_graphs_post():
	global  numSamples1, numSamples2

	numSamples2 = request.form['numSamples2']
	numSamples2 = datetime.strptime(numSamples2, "%Y-%m-%d")

	numSamples1_disp = str(numSamples1)[:10]
	numSamples2_disp = str(numSamples2)[:10]

	numSamples2 = numSamples2 + timedelta(days=1)

	lastDate, power = getLastData()
	firstDate, nada1 = getFirstData()
	power = round(power, 2)

	energyToday = getHistDataEnergyToday()

	templateData = {
		'power'						: power,
		'energytoday'				: energyToday,
		'minDateSel'				: numSamples1_disp,
		'maxDateSel'				: numSamples2_disp,
		'minDate'					: firstDate[:10],
		'maxDate'					: lastDate[:10],
		'maxDateFull'				: lastDate[11:],
		'sysTemp'					: getCPUTemp()
	}
	
	return render_template('matplotlib_downloadable.html', **templateData)

@app.route("/settings.html")
def settings():

	lastEdit, samplingPeriod, language = getSettings()
	energyToday = getHistDataEnergyToday()
	lastDate, power = getLastData()
	power = round(power, 2)
	

	templateData = {
		'power'						: power,
		'energytoday'				: energyToday,
		'maxDate'					: lastDate[:10],
		'maxDateFull'				: lastDate[11:],
		'sysTemp'					: getCPUTemp(),
		'samplingPeriod'			: samplingPeriod,
		'language'					: language
	}
	return render_template('settings.html', **templateData)

@app.route("/settings.html", methods=['POST'])
def settings_post():
	lastEdit, samplingPeriod, language = getSettings()
	energyToday = getHistDataEnergyToday()
	lastDate, power = getLastData()
	power = round(power, 2)

	try:
		samplingPeriod = int(request.form['samplingPeriod'])
	except ValueError:
		pass
	if samplingPeriod > 900:
		samplingPeriod = 900
	elif samplingPeriod < 10:
		samplingPeriod = 10

	language_new = request.form['language']
	if language_new in ['en','hu','sk']:
		language = language_new

	if request.form['save'] == 'Save changes':
		saveSettings(samplingPeriod, language)
	elif request.form['save'] == 'Reboot System' and sys() == 'Linux':
		saveSettings(samplingPeriod, language)
		os.system('sudo reboot')

	templateData = {
		'power'						: power,
		'energytoday'				: energyToday,
		'maxDate'					: lastDate[:10],
		'maxDateFull'				: lastDate[11:],
		'sysTemp'					: getCPUTemp(),
		'samplingPeriod'			: samplingPeriod,
		'language'					: language
	}
	return render_template('settings.html', **templateData)

@app.route("/usage.html")
def usage():
	templateData = basicTemplate()
	return render_template('usage.html', **templateData)

@app.route("/icons.html")
def icons():
	
	return render_template('icons.html')

@app.route("/notifications.html")
def notifications():
	
	return render_template('notifications.html')

@app.route("/tables.html")
def tables():
	
	return render_template('tables.html')

@app.route("/typography.html")
def typography():
	
	return render_template('typography.html')

@app.route("/user.html")
def user():
	
	return render_template('user.html')

@app.route('/database.db', methods=['GET', 'POST'])
def download():
	return send_from_directory("/home/pi", "dummy.db")

@app.route('/plot/power')
def plot_power():
	try:
		lock.acquire(True)
		times, power = getHistDataPower(numSamples1, numSamples2)
		for j in range(len(times)):
			times[j]=times[j][11:16]
		xs = times
		ys = power
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Power [kW] [Today]")
		axis.set_xlabel("Time [Hour:Minute]")
		axis.set_xticks([0, int(len(ys)/6), int(len(ys)/3), int(len(ys)/2), int(len(ys)/1.5), int(len(ys)/1.2), int(len(ys)/1.01)])
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
		ysCost = [x * costPerKwh for x in ys]
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Energy & Cost / day  [30 Days]")
		axis.set_xlabel("Date [Month : Day] ")
		axis.set_xticks([0, int(len(ys)/6), int(len(ys)/3), int(len(ys)/2), int(len(ys)/1.5), int(len(ys)/1.2), int(len(ys)/1.01)])
		axis.grid(True)
		p1 = axis.bar(xs, ys, width=0.5)
		p2 = axis.bar(xs, ysCost, width=0.5)
		axis.legend((p1[0], p2[0]), ('Energy [kWh]', 'Cost [€]'))
		canvas = FigureCanvas(fig)
		output = io.BytesIO()
		canvas.print_png(output)
		response = make_response(output.getvalue())
		response.mimetype = 'image/png'
		return response
	finally:
		lock.release()

@app.route('/plot/energydailyavg')
def plot_energyDailyAvg():
	try:
		lock.acquire(True)
		times, energy = getHistDataEnergyDailyAvg(numSamples1, numSamples2)
		for j in range(len(times)):
			times[j]=times[j][5:7]
		xs = times
		ys = energy
		ysCost = [x * costPerKwh for x in ys]
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Average Energy & Cost / Day / Month  [12 Months]")
		axis.set_xlabel("Date [Month]")
		axis.grid(True)
		p1 = axis.bar(xs, ys, width=0.5)
		p2 = axis.bar(xs, ysCost, width=0.5)
		axis.legend((p1[0], p2[0]), ('Energy [kWh]', 'Cost [€]'))
		canvas = FigureCanvas(fig)
		output = io.BytesIO()
		canvas.print_png(output)
		response = make_response(output.getvalue())
		response.mimetype = 'image/png'
		return response
	finally:
		lock.release()

@app.route('/plot/energymonthly')
def plot_energyDailyMonthly():
	try:
		lock.acquire(True)
		times, energy = getHistDataEnergyMonthly(numSamples1, numSamples2)
		for j in range(len(times)):
			times[j]=times[j][5:7]
		xs = times
		ys = energy
		ysCost = [x * costPerKwh for x in ys]
		fig = Figure()
		axis = fig.add_subplot(1, 1, 1)
		axis.set_title("Energy & Cost/ month  [12 Months]")
		axis.set_xlabel("Date [Year : Month]")
		axis.grid(True)
		p1 = axis.bar(xs, ys, width=0.5)
		p2 = axis.bar(xs, ysCost, width=0.5)
		axis.legend((p1[0], p2[0]), ('Energy [kWh]', 'Cost [€]'))
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
