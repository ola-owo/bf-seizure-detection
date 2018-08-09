#!/usr/bin/env python2

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

PTNAME_REGEX = re.compile(r'^[\w-]+$') # only allow letters, numbers, and "-" in patient name

patient = sys.argv[1]
if not re.match(PTNAME_REGEX, patient):
    raise Exception('Invalid patient name - must only contain letters, numbers, underscores, and/or dashes') 

bf = Blackfynn()
#conn = sqlite3.connect('mini-diary.db')
conn = sqlite3.connect(DIARY_DB_NAME)
c = conn.cursor()

def toDateTime(t):
    'convert epoch time to datetime object'
    return dt.datetime.utcfromtimestamp(t/1000000)

def makeScatter(seizures, durations, label, height=0):
    startTimes = map(toDateTime, seizures[:,0])
    endTimes = map(toDateTime, seizures[:,1])

    traces = []
    for i in range(len(startTimes)):
        trace = go.Scatter(
            x = (startTimes[i], endTimes[i]),
            y = (height,height),
            hoverinfo = 'x+text+name',
            mode = 'lines+markers',
            text = ['Duration: %d s' % durations[i],
                    'Duration: %d s' % durations[i]],
            marker = {
                'color': durations[i],
                'colorscale': 'Viridis',
                'cmin': 0,
                'cmax': 600,
                'showscale': False
            }
        )
        if i % 2 == 0:
            trace.name = 'Seizure start'
        else:
            trace.name = 'Seizure end'
        traces.append(trace)
    return traces

def seizuresPer(interval, seizures):
    'Calculate seizures per day, week, month'
    total = seizures.shape[0]
    # Days between 1st and last seizure:
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

print 'Updating seizure diary for', patient
ts = bf.get(TS_IDs[patient])

# Plot all seizures
seizures = c.execute('SELECT start, end FROM ' + patient + ' ORDER BY end').fetchall()
if seizures:
    seizures = np.array(seizures, dtype='int')
else:
    print 'No seizures to plot.'
    conn.close()
    sys.exit()

# Make figure with subplots
#fig = tools.make_subplots(rows=4, cols=3, specs=[
#    [{'rowspan': 3, 'colspan': 2}, None, {'rowspan': 3}],
#    [None, None, None],
#    [None, None, None],
#    [{'colspan': 3}, None, None]
#])

# Plot seizure times
durations = (seizures[:,1] - seizures[:,0]) / 1000000
data = makeScatter(seizures, durations, 'Auto-detected seizure')
#for tr in makeScatter(seizures, durations, 'Auto-detected seizure'):
#    fig.append_trace(tr, 1, 1)

# Plot gold standard seizures (if any):
layerID = GOLD_STD_LAYERS.get(patient, None)
if layerID is not None:
    layer = ts.get_layer(layerID)
    goldSeizures = np.array([(a.start, a.end) for a in layer.annotations()])
    goldDurations = (goldSeizures[:,1] - goldSeizures[:,0]) / 1000000
    data += makeScatter(goldSeizures, goldDurations, 'Gold-standard seizure',
                        height=-1)
    #for tr in makeScatter(goldSeizures, goldDurations, 'Gold-standard seizure',
    #                      height=-1):
    #    fig.append_trace(tr, 1, 1)

# Plot histogram
hist = go.Histogram(x=durations, xaxis='x2', yaxis='y2', hoverinfo = 'y')
data.append(hist)
#fig.append_trace(hist, 1, 3)

# Make seizure stats table
table = go.Table(
    header = {'values': ['Total seizures', 'Seizures/day',
                         'Seizures/week', 'Seizures/month']},
    cells = {'values': [
        seizures.shape[0],
        round(seizuresPer('day', seizures), 2),
        round(seizuresPer('week', seizures), 2),
        round(seizuresPer('month', seizures), 2)
    ]},
    #domain = {'y': (0, 0.3)}
    domain = {'y': (0.7, 1)}
)
#table = ff.create_table([
#    ['Total', 'Per day', 'Per week', 'Per month'], [
#        seizures.shape[0],
#        round(seizuresPer('day', seizures), 2),
#        round(seizuresPer('week', seizures), 2),
#        round(seizuresPer('month', seizures), 2)
#    ]])

data.append(table)
#fig.append_trace(table['data'][0], 4, 1)

# Setup layout and plot figure
layout = go.Layout(
    title = 'Seizure Diary: ' + patient,
    hovermode = 'closest',
    showlegend = False,
    xaxis = dict(
        domain = (0, 0.7),
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
        'domain': (0.75, 1),
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
#fig.layout = layout
off.plot(fig, filename=(patient+'_diary'))

conn.close()
