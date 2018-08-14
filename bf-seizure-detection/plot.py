#!/usr/bin/env python2
'Usage: ./plot.py patientName algo'

import datetime as dt
import re
import sys
import sqlite3

from blackfynn import Blackfynn
from matplotlib.dates import DateFormatter, date2num
import numpy as np
from plotly import tools
import plotly.figure_factory as ff
import plotly.offline as off
import plotly.graph_objs as go

from settings import (
    CHANNELS, DIARY_DB_NAME, GOLD_STD_LAYERS, LIVE_UPDATE_TIMES, LL_LAYER_NAME,
    LL_MA_LAYER_NAME, PL_LAYER_NAME, PL_ROOT, SZ_PLOT_ROOT, TS_IDs
)
from tools import toDateTime

PTNAME_REGEX = re.compile(r'^[\w-]+$') # only allow letters, numbers, and "-" in patient name

patient = sys.argv[1]
algo = sys.argv[2]

if not re.match(PTNAME_REGEX, patient):
    raise Exception('Invalid patient name - must only contain letters, numbers, underscores (_), and/or dashes (-)') 

def makeScatter(seizureTimes, durations, label, height=0):
    timestamps = map(toDateTime, seizureTimes)
    trace = go.Scatter(
        x = timestamps,
        y = [height] * len(timestamps),
        hoverinfo = 'x+text+name',
        mode = 'markers',
        name = label,
        text = ['Duration: %d s'%d for d in durations],
        marker = {
            'color': durations,
            'colorbar': {'title':'Duration (sec)'},
            'colorscale': 'Viridis',
            'cmin': 0,
            'cmax': 600,
            'showscale': True
        }
    )
    return trace

def seizuresPer(interval, seizures):
    'Calculate seizures per day, week, month'
    total = seizures.shape[0]
    if total == 0: return 0.0

    days = float(dt.timedelta(
        microseconds = seizures[-1,0] - seizures[0,0]
    ).days)

    perDay = total / days
    if interval == 'day':
        return perDay
    elif interval == 'week':
        return perDay * 7
    elif interval == 'month':
        return perDay * 365 / 12
    else:
        raise ValueError("Interval must be 'day', 'week', or 'month'")

print 'Creating seizure diary for', patient
print 'Classifier:', algo

# Get seizures from database
conn = sqlite3.connect(DIARY_DB_NAME)
c = conn.cursor()

seizures = c.execute("SELECT start, end FROM " + patient + " WHERE type = '"+algo+"' ORDER BY end").fetchall()
seizures = np.array(seizures, dtype='int')

goldSeizures = c.execute("SELECT start, end FROM " + patient + " WHERE type = 'gold' ORDER BY end").fetchall()
goldSeizures = np.array(goldSeizures, dtype='int')

c.close()
conn.close()
if seizures.size == 0:
    print 'No seizures to plot.'
    sys.exit()

# Plot seizures
data = []
durations = (seizures[:,1] - seizures[:,0]) / 1000000
scatter = makeScatter(seizures[:,0], durations, 'Detected seizure')
data.append(scatter)

if goldSeizures.size > 0:
    goldDurations = (goldSeizures[:,1] - goldSeizures[:,0]) / 1000000
    goldScatter = makeScatter(goldSeizures[:,0], goldDurations, 'Pre-labeled seizure',
                        height=1)
    data.append(goldScatter)

# Plot histogram
hist = go.Histogram(x=durations, xaxis='x2', yaxis='y2', hoverinfo = 'y')
data.insert(0,hist)

# Make seizure stats table
table = go.Table(
    header = {'values': ['Total seizures', 'Seizures/day',
                         'Seizures/week', 'Seizures/month']},
    cells = {
        'values': [[
            seizures.shape[0],
            round(seizuresPer('day', seizures), 2),
            round(seizuresPer('week', seizures), 2),
            round(seizuresPer('month', seizures), 2)]],
        'fill': {'color': ['#d3d3d3', 'white']},
        'align': ['left', 'center']
    },
    #domain = {'y': (0, 0.3)}
    domain = {'y': (0.7, 1)}
)

data.append(table)

# Setup layout and plot figure
layout = go.Layout(
    title = 'Seizure Diary: ' + patient,
    hovermode = 'closest',
    showlegend = False,
    xaxis = dict(
        domain = (0.25, 1),
        title = 'Time (UTC)',
        rangeselector = {'buttons': [
            dict(count=1,
                 label='1d',
                 step='day',
                 stepmode='backward'),
            dict(count=7,
                 label='1w',
                 step='day',
                 stepmode='backward'),
            dict(count=1,
                label='1m',
                step='month',
                stepmode='backward'),
            dict(step='all')
        ]},
        rangeslider = {'visible': True},
    ),
    yaxis = dict(
        domain = (0, 0.6),
        #domain = (0.4, 1),
        autorange = True,
        showgrid = False,
        zeroline = True,
        ticks = '',
        showticklabels = False
    ),
    xaxis2 = {
        'domain': (0, 0.25),
        'title': 'Seizure duration (sec)'
    },
    yaxis2 = {
        'domain': (0, 0.6),
        #'domain': (0.4, 1),
        'anchor': 'x2',
        'title': 'Count'
    }
)
fig = go.Figure(data, layout)
off.plot(fig, filename=(patient+'_diary'), auto_open=False)
