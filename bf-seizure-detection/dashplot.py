#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import datetime as dt
import json
import sys
import sqlite3

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import hickle
import numpy as np
from plotly import figure_factory as ff
import plotly.graph_objs as go

from settings import (
    DIARY_DB_NAME, GOLD_STD_LAYERS, PL_LAYER_NAME, LL_LAYER_NAME,
    LL_MA_LAYER_NAME, TS_IDs
)
from tools import toDateTime, toUsecs

patients = sorted(TS_IDs)
app = dash.Dash()
app.scripts.config.serve_locally = True

dropdown = dcc.Dropdown(
    id='patient-switcher',
    options=[{'label': pt, 'value': pt} for pt in patients],
    placeholder='Current patient'
)

app.layout = html.Div([
    html.Div(id='top-row', children=[
        dcc.Graph(id='sz-hist'),


        html.Div(id='selector', children=[
            dropdown,
            html.Button('Reset Zoom', id='reset-button')]),

        dcc.Graph(id='sz-table'),

        dcc.Graph(id='roc-plot')
        ]),

    dcc.Graph(id='sz-plot'),

    html.Div(id='current-data'),
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
        unselected = {'marker': {'opacity': 0.3}},
        marker = {
            'color': durations,
            'colorbar': {'title':'Duration (sec)'},
            'colorscale': 'Electric',
            'reversescale': True,
            'cmin': 0,
            'cmax': 600,
            'showscale': True,
            'size': 8 + np.log10(durations),
            'line': {'width':1, 'color':'black'},
            'opacity': 1
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
    if days == 0: days = 1.0 # prevents division by zero errors

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
        currAnnots = layer.annotations(start=t)
    else:
        currAnnots = layer.annotations()

    while currAnnots:
        annots += currAnnots
        t = currAnnots[-1].end
        currAnnots = layer.annotations(start=t)
    return annots

def updateDB(bf, patient, algo):
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
    conn = sqlite3.connect(DIARY_DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS ' + patient + ' (start INT, end INT, type TEXT)')

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

@app.callback(Output('current-data', 'children'),
              [Input('patient-switcher', 'value'),
               Input('sz-plot', 'selectedData')])
def getData(patient, selectedData):
    'Update "current-data" div when switching patients or date range'
    def parse(p):
        'convert a datapoint to a (start,end) tuple (in usecs)'
        a = toUsecs(dt.datetime.strptime(p['x'], '%Y-%m-%d %H:%M:%S'))
        delta = int(p['text'].split()[1]) * 1000000 # parse seizure duration from hover text
        b = a + delta
        return (a, b)

    if patient is None:
        liveSz = []
        goldSz = []
    else:
        if selectedData:
            liveSz = [parse(p) for p in selectedData['points']
                      if p['curveNumber'] == 0]
            goldSz = [parse(p) for p in selectedData['points']
                      if p['curveNumber'] == 2]
        else: # no selection made
            liveSz = allSeizures[patient]['live'].tolist()
            goldSz = allSeizures[patient]['gold'].tolist()

    if patient in allROCs:
        roc = allROCs[patient]
    else:
        roc = None

    dct = {'live': liveSz, 'gold': goldSz, 'roc': roc}
    return json.dumps(dct)

@app.callback(Output('sz-plot', 'selectedData'),
              [Input('reset-button', 'n_clicks')],
              [State('patient-switcher', 'value')])
def reset(_, patient):
    return None

@app.callback(Output('sz-plot', 'figure'),
              [Input('current-data', 'children')])
def remakeSzPlot(json_data):
    data = json.loads(json_data)
    seizures = np.array(data['live']).reshape(-1,2)
    goldSeizures = np.array(data['gold']).reshape(-1,2)

    # Scatter plot data
    plot = []
    if seizures.size > 0:
        durations = (seizures[:,1] - seizures[:,0]) / 1000000
        plot.append(makeScatter(seizures[:,0], durations, 'Detected seizure', height=0.5))
        plot.append(go.Scatter())
    if goldSeizures.size > 0:
        goldDurations = (goldSeizures[:,1] - goldSeizures[:,0]) / 1000000
        plot.append(makeScatter(goldSeizures[:,0], goldDurations, 'Pre-labeled seizure',
                            height=1))

    # Scatter plot layout
    layout = go.Layout(
        title = 'Seizure History',
        hovermode = 'closest',
        dragmode = 'select',
        selectdirection = 'h',
        showlegend = False,
        margin = {'l':100, 'r':0},
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
            #rangeslider = {'visible': True},
            gridcolor = '#ccc',
            gridwidth = 2,
        ),
        yaxis = dict(
            title = 'Annotation type',
            fixedrange = True,
            range = (0,1.5),
            showgrid = False,
            #ticks = '',
            showticklabels = True,
            tickvals = (0.5, 1),
            ticktext = ('Auto-detected', 'Pre-labeled'),
            tickangle = -45
        ),
    )
    scatter = go.Figure(plot, layout)
    return scatter

@app.callback(Output('sz-hist', 'figure'),
              [Input('current-data', 'children')])
def remakeHist(json_data):
    data = json.loads(json_data)
    seizures = np.array(data['live']).reshape(-1,2)
    goldSeizures = np.array(data['gold']).reshape(-1,2)

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

def tableData(arr):
    'Helper function for remakeTable()'
    if arr.size > 0:
        data = [arr.shape[0],
                round(np.mean((arr[:,1] - arr[:,0]) / 1000000), 2),
                round(seizuresPer('day', arr), 2),
                round(seizuresPer('week', arr), 2),
                round(seizuresPer('month', arr), 2)]
    else:
        data = [0,0,0,0,0]
    return data

@app.callback(Output('sz-table', 'figure'),
              [Input('current-data', 'children')])
def remakeTable(json_data):
    data = json.loads(json_data)
    seizures = np.array(data['live']).reshape(-1,2)
    goldSeizures = np.array(data['gold']).reshape(-1,2)

    table = ff.create_table([
        ['Annotation<br>type', 'Total', 'Mean length<br>(sec)', 'Avg/day', 'Avg/week', 'Avg/month'],
        ['Pre-labeled'] + tableData(goldSeizures),
        ['Auto-detected'] + tableData(seizures)
    ], index=True, index_title='TYPE')
    return table

@app.callback(Output('roc-plot', 'figure'),
              [Input('current-data', 'children')])
def remakeROC(json_data):
    data = json.loads(json_data)
    if data['roc'] is None:
        xdata = ydata = []
    else:
        xdata = data['roc']['fp']
        ydata = data['roc']['tp']

    trace = go.Scatter(
        x = xdata,
        y = ydata,
        hoverinfo = 'x+y',
        name = 'ROC',
        mode = 'lines'
    )

    # Scatter plot layout
    layout = go.Layout(
        title = 'ROC',
        hovermode = 'closest',
        xaxis = {'title': 'False positive rate'},
        yaxis = {'title': 'True positive rate'}
    )
    scatter = go.Figure([trace], layout)
    return scatter

if __name__ == '__main__':
    # Load all seizures from DB, then start server
    try:
        algo = sys.argv[1]
        if algo not in ('pipeline', 'linelength', 'ma_linelength'):
            raise ValueError("Invalid classifier '%s'" % algo)
    except IndexError:
        algo = 'pipeline'
        print "No classifier selected, defaulting to 'pipeline'"

    conn = sqlite3.connect(DIARY_DB_NAME)
    c = conn.cursor()

    allSeizures = {}
    allROCs = {}
    for patient in patients:
        # Load seizures
        goldSz = c.execute("SELECT start, end FROM " + patient + \
            " WHERE type = 'gold'").fetchall()
        liveSz = c.execute("SELECT start, end FROM " + patient + \
            " WHERE type = '"+algo+"'").fetchall()

        allSeizures[patient] = {}
        allSeizures[patient]['gold'] = np.array(goldSz)
        allSeizures[patient]['live'] = np.array(liveSz)

        # Load ROC data
        try:
            roc = hickle.load(patient + '_roc.hkl')
            for k,v in roc.items(): roc[k] = v.tolist()
            allROCs[patient] = roc
        except:
            pass

    c.close()
    conn.commit()
    conn.close()
    app.run_server(debug=True)
