#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import datetime as dt
import json
import sys
import sqlite3

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
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
    value=patients[1],
)

app.layout = html.Div(children=[
    html.Div([
        html.Label('Current Patient:', style={'text-align':'center'}),
        dropdown,
        html.Label('Date Range:'),
        dcc.DatePickerRange(id='date-range',
            initial_visible_month=dt.datetime.utcnow(),
            start_date_placeholder_text='Start date',
            end_date_placeholder_text='End date',
            max_date_allowed=(dt.datetime.utcnow()+dt.timedelta(days=1)),
            ),
        html.Button('Reset', id='reset-button')
        ], style={'width':'10em', 'margin':'0 auto 3em auto'}),


    html.Div([
        dcc.Graph(id='sz-hist', style={'height':'100%', 'width':'45%'}),
        dcc.Graph(id='sz-table', style={'width':'45%'})

        ], style={'display':'flex', 'justify-content':'space-between',
                  'height':'40vh', 'margin-bottom':'1%'}),

    dcc.Graph(id='sz-plot'),

    html.Div(id='current-data', style={'display':'none'}),
], style={'background-color':'#f3f3f3', 'padding':'1%'})

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
            'colorscale': 'Electric',
            'reversescale': True,
            'cmin': 0,
            'cmax': 600,
            'showscale': True,
            'size': 8 + np.log10(durations),
            'line': {'width':1, 'color':'black'}
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

@app.callback(Output('date-range', 'start_date'),
              [Input('reset-button', 'n_clicks')])
def resetstartDate(_):
    return None

@app.callback(Output('date-range', 'end_date'),
              [Input('reset-button', 'n_clicks')])
def resetEndDate(_):
    return None

def timeFilter(arr, start_date, end_date):
    'helper function for getData()'
    if arr.size == 0: return arr

    if start_date and end_date:
        idx = np.logical_and((arr[:,0] >= start_date), (arr[:,0] < end_date))
    elif start_date and not end_date:
        idx = (arr[:,0] >= start_date)
    elif not start_date and end_date:
        idx = (arr[:,0] < end_date)
    else:
        idx = None
    return arr[idx]

@app.callback(Output('current-data', 'children'),
              [Input('patient-switcher', 'value'),
               Input('date-range', 'start_date'),
               Input('date-range', 'end_date')])
def getData(patient, start_str, end_str):
    def parse(dateStr):
        return dt.datetime.strptime(dateStr, '%Y-%m-%d')

    if start_str:
        start_time = toUsecs(parse(start_str))
    else:
        start_time = None
    if end_str:
        end_time = toUsecs(parse(end_str))
    else:
        end_time = None

    liveSz = allSeizures[patient]['live']
    goldSz = allSeizures[patient]['gold']

    liveSz = timeFilter(liveSz, start_time, end_time)
    goldSz = timeFilter(goldSz, start_time, end_time)

    dct = {'live': liveSz.tolist(), 'gold': goldSz.tolist()}
    return json.dumps(dct)

@app.callback(Output('sz-plot', 'figure'),
              [Input('current-data', 'children')])
def remakeScatter(json_data):
    data = json.loads(json_data)
    seizures = np.array(data['live']).reshape(-1,2)
    goldSeizures = np.array(data['gold']).reshape(-1,2)
    print 'seizures size:', seizures.shape

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
            #rangeslider = {'visible': True},
        ),
        yaxis = dict(
            range = (0,1.5),
            showgrid = False,
            zeroline = False,
            #ticks = '',
            showticklabels = True,
            tickvals = (0.5, 1),
            ticktext = ('Auto-detected', 'Pre-labeled')
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
                np.mean((arr[:,1] - arr[:,0]) / 1000000),
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
        ['Annotation type', 'Total seizures', 'Mean length (sec)', 'Seizures/day', 'Seizures/week', 'Seizures/month'],
        ['Pre-labeled'] + tableData(goldSeizures),
        ['Auto-detected'] + tableData(seizures)
    ])
    return table

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
