#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import datetime as dt
import sys
import sqlite3

from blackfynn import Blackfynn
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
from plotly import figure_factory as ff
import plotly.graph_objs as go

from settings import TS_IDs, DIARY_DB_NAME
from tools import toDateTime

bf = Blackfynn()
patients = sorted(TS_IDs)
app = dash.Dash()
app.scripts.config.serve_locally = True

dropdown = dcc.Dropdown(
    id='patient-switcher',
    options=[{'label': pt, 'value': pt} for pt in patients],
    value=patients[1]
)

app.layout = html.Div(children=[
    html.H1(children='Seizure Diary', style={'text-align':'center'}),
    html.Label('Current patient:'),
    dropdown,

    dcc.Graph(id='sz-plot'),

    dcc.Graph(id='sz-hist',
        style={'height':'40vh', 'width':'45%', 'float':'left'}),

    dcc.Graph(id='sz-table',
        style={'width':'45%', 'float':'right'}),

    html.Div(id='my-div')
])

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

def getAnnots(patient, layer, type_, c):
    'Get all annotations of type type_ that are not already in the database'
    annots = []
    lastSz = c.execute("SELECT end FROM "+patient+" WHERE type = '"+type_+"' ORDER BY end DESC").fetchone()
    if lastSz:
        t = lastSz[0]
        anns = layer.annotations(start=t)
    else:
        anns = layer.annotations()

    while anns:
        annots += anns
        t = anns[-1].end
        anns = layer.annotations(start=t)
    return annots

def updatePatient(bf, algo, patient):
    '''
    Retreive patient's current gold standard and auto-detected seizures,
    and save them in the database.
    '''
    if algo == 'pipeline':
        liveLayerName = PL_LAYER_NAME
    elif algo == 'linelength':
        liveLayerName = LL_LAYER_NAME
    elif algo == 'ma_linelength':
        liveLayerName = LL_MA_LAYER_NAME
    else:
        raise ValueError("Invalid classifier '%s'" % algo)

    ts = bf.get(TS_IDs[patient])
    conn = sqlite3.connect('mini-diary.db') # DEBUG
    #conn = sqlite3.connect(DIARY_DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS ' + ptName + ' (start INT, end INT)')

    # Get gold standards
    layerID = GOLD_STD_LAYERS.get(patient, None)
    if layerID:
        layer = ts.get_layer(layerID)
        goldSeizures = getAnnots(patient, layer, 'gold', c)
        for sz in goldSeizures:
            c.execute('INSERT INTO '+patient+' VALUES (?,?,?)', (sz.start, sz.end, 'gold'))

    # Get auto-detected seizures
    try:
        layer = ts.get_layer(liveLayerName)
        seizures = getAnnots(patient, layer, algo, c)
    except: # if live layer doesn't exist
        seizures = []
    for sz in seizures:
        c.execute('INSERT INTO '+patient+' VALUES (?,?,?)', (sz.start, sz.end, algo))

    c.close()
    conn.commit()
    conn.close()

@app.callback(Output('sz-plot', 'figure'),
              [Input('patient-switcher', 'value')])
def remakeScatter(patient):
    seizures = allSeizures[patient]['live']
    goldSeizures = allSeizures[patient]['gold']

    # Scatter plot data
    plot = []
    if seizures.size > 0:
        durations = (seizures[:,1] - seizures[:,0]) / 1000000
        plot.append(makeScatter(seizures[:,0], durations, 'Detected seizure'))
        plot.append(go.Scatter())
    if goldSeizures.size > 0:
        goldDurations = (goldSeizures[:,1] - goldSeizures[:,0]) / 1000000
        plot.append(makeScatter(goldSeizures[:,0], goldDurations, 'Pre-labeled seizure',
                            height=1))

    # Scatter plot layout
    layout = go.Layout(
        title = 'Seizure History: ' + patient,
        hovermode = 'closest',
        showlegend = False,
        plot_bgcolor = '#f3f3f3',
        xaxis = dict(
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
            autorange = True,
            showgrid = False,
            zeroline = True,
            ticks = '',
            showticklabels = False
        ),
    )
    scatter = go.Figure(plot, layout)
    return scatter

@app.callback(Output('sz-hist', 'figure'),
              [Input('patient-switcher', 'value')])
def remakeHist(patient):
    seizures = allSeizures[patient]['live']
    if seizures.size > 0:
        durations = (seizures[:,1] - seizures[:,0]) / 1000000
    else:
        durations = []

    trace = go.Histogram(x=durations, hoverinfo = 'y')
    layout = go.Layout(
        title = 'Seizure Lengths',
        hovermode = 'closest',
        showlegend = False,
        xaxis = {'title': 'Duration (sec)'},
        yaxis = {'title': 'Count'}
    )
    hist = go.Figure([trace], layout)
    return hist

@app.callback(Output('sz-table', 'figure'),
              [Input('patient-switcher', 'value')])
def remakeTable(patient):
    seizures = allSeizures[patient]['live']
    if seizures.size > 0:
        durations = (seizures[:,1] - seizures[:,0]) / 1000000
        data = [seizures.shape[0],
         round(seizuresPer('day', seizures), 2),
         round(seizuresPer('week', seizures), 2),
         round(seizuresPer('month', seizures), 2)]
    else:
        data = [0,0,0,0]

    table = ff.create_table([
        ['Total seizures', 'Seizures/day', 'Seizures/week', 'Seizures/month'],
        data])
    return table

if __name__ == '__main__':
    # Load all seizures from DB, then start server
    algo = sys.argv[1]
    if algo not in ('pipeline', 'linelength', 'ma_linelength'):
        raise ValueError("Invalid classifier '%s'" % algo)

    conn = sqlite3.connect('mini-diary.db') # DEBUG
    #conn = sqlite3.connect(DIARY_DB_NAME)
    c = conn.cursor()

    allSeizures = {}
    for patient in patients:
        goldSz = c.execute("SELECT start, end FROM " + patient + \
            " WHERE type = 'gold'").fetchall()
        liveSz = c.execute("SELECT start, end FROM " + patient + \
            " WHERE type = '"+algo+"'").fetchall()

        allSeizures[patient] = {}
        allSeizures[patient]['gold'] = np.array(goldSz)
        allSeizures[patient]['live'] = np.array(liveSz)

    c.close()
    conn.commit()
    conn.close()
    app.run_server(debug=True)
