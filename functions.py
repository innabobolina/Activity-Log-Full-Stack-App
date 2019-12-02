
"""
# functions for server.py
"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Activity, Event

from darksky import forecast

import datetime
from dateutil import tz

from twilio.rest import Client

import os
import password_hashing
from twilio.twiml.messaging_response import MessagingResponse

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
my_twilio_number = os.environ["MY_TWILIO_NUMBER"]
my_mobile_number = os.environ["MY_MOBILE_NUMBER"]

TZ_PST = tz.gettz("America/Los_Angeles")


# --------------------------------------------------------------
def get_weather(lng, lat):
    """Return current temperature in F and probability of rain in %"""

    mykey = '1e961549f122c0b437df44466bf6fa45'
    sf = forecast(mykey, lat, lng)
    rain_proba = int(sf.currently.precipProbability * 100) # 0.03
    temp = int(sf.currently.temperature)

    return rain_proba, temp

# --------------------------------------------------------------
def get_forecast(lng, lat):
    """Return weather forecast for the next week"""

    mykey = '1e961549f122c0b437df44466bf6fa45'
    weekday = datetime.date.today()
    sf = forecast(mykey, lat, lng)
    html_str = ""

    with forecast(mykey, lat, lng) as sf:
         html_str += str(sf.daily.summary) + "<br>---<br>\n"
         for day in sf.daily:
             day = dict(day = datetime.date.strftime(weekday, '%a'),
                        sum = day.summary,
                        tempMin = day.temperatureMin,
                        tempMax = day.temperatureMax
                        )
             html_str += "{day}: {sum} Temp range: {tempMin} - {tempMax}".format(**day)
             html_str += "<br>\n"
             weekday += datetime.timedelta(days=1)

    return html_str

# --------------------------------------------------------------
def format_data(tup_lst):
    """Combine events for the same date in one date, 
        sort events chronologically"""

    # combine events for the same date in one date:
    dct = {}
    for tup in tup_lst:
        evt_date = tup[0]
        evt_amt  = tup[1]
        if evt_date in dct:
            dct[evt_date] += evt_amt
        else:
            dct[evt_date] = evt_amt
    tup_lst = [(k,v) for k,v in dct.items()]

    # sort by the first item in the tuple i.e. chronologically by date:
    tuples_list_sorted = sorted(tup_lst, key = lambda x: x[0])
    x = []
    y = []
    for tup in tuples_list_sorted:
        x += [ tup[0].strftime("%m/%d/%Y") ]
        y += [ tup[1] ]
    return x,y
# --------------------------------------------------------------
def last_n_days(current_events, n_days):
    """Return event dates and event amounts for the last n_days"""

    date_now = datetime.datetime.now().date()
    n_days_ago = date_now - datetime.timedelta(n_days)

    # loop over events, select only those within last n_days:
    chart_tuples = []
    for e in current_events:
        if n_days_ago <= e.event_date.date() <= date_now :
            chart_tuples.append((e.event_date, e.event_amt))

    xN,yN = format_data(chart_tuples)

    return xN,yN 
# --------------------------------------------------------------
def add_stats_attributes_to_user_activities(u):
    for a in u.activities:
        a.count = 0
        a.total = 0
        a.mean  = 0
        a.max   = 0
        for e in a.events:
            a.total += e.event_amt
            a.count += 1
            if e.event_amt > a.max:
                a.max = e.event_amt        
        if a.count > 0:
            a.mean = a.total / a.count

# --------------------------------------------------------------
# --------------------------------------------------------------
# --------------------------------------------------------------
