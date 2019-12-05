
"""Functions for server.py."""

from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
import os

from model import connect_to_db, db, User, Activity, Event

from darksky import forecast
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

import password_hashing
import datetime
from dateutil import tz


# account_sid = os.environ['TWILIO_ACCOUNT_SID']
# auth_token = os.environ['TWILIO_AUTH_TOKEN']
# my_twilio_number = os.environ["MY_TWILIO_NUMBER"]
# my_mobile_number = os.environ["MY_MOBILE_NUMBER"]


from dotenv import load_dotenv
load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
my_twilio_number = os.getenv("MY_TWILIO_NUMBER")
my_mobile_number = os.getenv("MY_MOBILE_NUMBER")
mykey = os.getenv('DARKSKY_API_KEY')

TZ_PST = tz.gettz("America/Los_Angeles")


# --------------------------------------------------------------
def get_weather(lng, lat):
    """Return current temperature in F and probability of rain in %"""

    sf = forecast(mykey, lat, lng)
    rain_proba = int(sf.currently.precipProbability * 100) # 0.03
    temp = int(sf.currently.temperature)

    return rain_proba, temp

# --------------------------------------------------------------
def get_forecast(lng, lat):
    """Return weather forecast for the next week"""

    weekday = datetime.date.today()
    sf = forecast(mykey, lat, lng)
    html_str = ""

    forecast_data = {}
    with forecast(mykey, lat, lng) as sf:
        forecast_data["daily_summary"] = sf.daily.summary
        forecast_data["daily_forecast"] = []

        html_str += "7 day weather forecast SUMMARY: " + str(sf.daily.summary) + "<br>\n"
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
def create_act_summary(user): 
    date_now = datetime.datetime.now().date()
    date7    = date_now - datetime.timedelta(7)

    act_summary = "For the last 7 days: \n"
    any_activity_recorded = False
    for activity in user.activities:
        a_total = 0
        add_to_message = False
        for e in activity.events:
            if date7 <= e.event_date.date() <= date_now: 
                add_to_message = True
                a_total += e.event_amt

        if add_to_message: 
            any_activity_recorded = True
            act_summary += \
            f" {activity.act_name}: total of {a_total:g} {activity.act_unit}\n"


    if not any_activity_recorded:
        print("no activity found")
    else:
        print(act_summary)

    return act_summary

# --------------------------------------------------------------
# --------------------------------------------------------------
