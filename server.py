"""Activity Log"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Activity, Event

from darksky import forecast

import datetime
from dateutil import tz
TZ_PST = tz.gettz("America/Los_Angeles")

# /usr/bin/env python
# Download the twilio-python library from twilio.com/docs/libraries/python

from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined



def get_weather(lng, lat):
    """Return current temperature in F and probability of rain in %"""

    mykey = '1e961549f122c0b437df44466bf6fa45'
    sf = forecast(mykey, lat, lng)
    rain_proba = int(sf.currently.precipProbability * 100) # 0.03
    temp = int(sf.currently.temperature)

    return rain_proba, temp


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


#########################
# http://0.0.0.0:5000/
#########################
@app.route('/', methods=['GET'])
def index():
    """Homepage showing a log in form."""

    return render_template("homepage.html")
    # return "<html><body>Placeholder for the homepage.</body></html>"



@app.route('/login', methods=['POST'])
def login_process():
    """Process login."""

    # Get form variables
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No such user, please register")
        return redirect("/")

    if user.password != password:
        flash("Incorrect password")
        return redirect("/")

    session["user_id"] = user.user_id

    flash("Logged in")
    print("logged in", email)
    return redirect("/activity")
    # return redirect(f"/users/{user.user_id}")


@app.route('/logout')
def logout():
    """Log out."""

    del session["user_id"]
    flash("Logged Out.")
    return redirect("/")


###############################
# http://0.0.0.0:5000/register
###############################
@app.route('/register', methods=['GET'])
def register_form():
    """Show form for user signup."""

    return render_template("register.html")


@app.route('/register', methods=['POST'])
def register_process():
    """Process registration."""

    # Get form variables
    email    = request.form["email"]
    password = request.form["password"]
    username = request.form["username"]
    
    user_exists = User.query.filter_by(email=email).first()

    if user_exists:
        flash(f"""User {email} already exists. 
            Please log in, you don't need to register! :)""")
        return redirect("/")

    new_user = User(email=email, password=password, username=username)

    for act_name, act_unit in Activity.DEFAULT_ACTIVITIES:
        activity = Activity(act_name=act_name, act_unit=act_unit)
        new_user.activities.append(activity)

    db.session.add(new_user)
    db.session.commit()

    flash(f"User {email} added. Now please log in.")
    return redirect("/")


###############################
# http://0.0.0.0:5000/activity
###############################
@app.route('/activity', methods=['GET'])
def act():
    """Page displaying a list of activities."""

    if "user_id" in session:
        user = User.query.get(session["user_id"])

        return render_template("activity.html", user=user)

    return redirect('/')


@app.route('/activity', methods=['POST'])
def get_activity():
    """Process adding a new activity."""

    user = User.query.get(session["user_id"])

    # Get form variables
    activity = request.form["activity"]
    unit = request.form["unit"]

    act_exists = Activity.query.filter_by(act_name=activity, act_unit=unit).first()

    if act_exists:
        flash("Activity already exists")

    if not act_exists:

        new_act = Activity(act_name=activity, act_unit=unit)
        user.activities.append(new_act)

        db.session.add(new_act)
        db.session.commit()

        flash(f"Activity {activity} added.")

    print(act_exists)
    return redirect("/activity")


###############################
# http://0.0.0.0:5000/event
###############################
@app.route('/event', methods=['GET'])
def event():
    """Page to log an event of a selected activity."""

    if "user_id" in session:
        user = User.query.get(session["user_id"])

        return render_template("event.html", user=user)
    return redirect('/')


@app.route('/event', methods=['POST'])
def get_event():

    # Get form variables
    act_id     = request.form.get("activity")
    event_date = request.form.get("date")
    amount     = request.form.get("amount")
    print(f"act_id={act_id}, event_date={event_date}, amount={amount}")
    
    new_event = Event(event_amt=amount, event_date=event_date)

    a = Activity.query.get(int(act_id))
    print(a.act_name)
    a.events.append(new_event)
    db.session.add(new_event)
    db.session.commit()

    flash(f"Event {a.act_name} {event_date} added")

    return redirect("/dashboard")


###########################################
# http://0.0.0.0:5000/api/activity?act_id=1
###########################################
@app.route('/api/activity', methods=['GET'])
def api_activity():

    act_id = request.args.get("act_id")

    a = Activity.query.get(int(act_id))

    dct = {"act_id": a.act_id,
           "act_name": a.act_name,
           "act_unit": a.act_unit }

    return jsonify(dct)


@app.route('/api/events', methods=['GET'])
def api_events():

    act_id = request.args.get("act_id")

    a = Activity.query.get(int(act_id))

    print(a)

    dct = {
    # "a.events.event_date": a.events.event_date,
    "act_id": a.act_id,
           "act_name": a.act_name,
           "act_unit": a.act_unit }


    return jsonify(dct)



################################
# http://0.0.0.0:5000/dashboard
################################
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Display events by activity"""
    
    if "user_id" not in session:
        return redirect('/')

    u = User.query.get(session["user_id"])
    
    print(f"user_id={u.user_id}, username={u.username}, email={u.email}")
    # print(u.activities)  # prints a list of reprs of all activities

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

        # a.total = sum(e.event_amt for e in a.events)             

                                  # longitude  latitude
    lng = -122.4194
    lat = 37.7749

    rain_proba, temp = get_weather(lng, lat)
    forecast_html_str = get_forecast(lng, lat)

    now_utc = datetime.datetime.now()
    now_pst = now_utc.astimezone(TZ_PST)
    dt_str =  now_pst.strftime('%Y-%m-%d %H:%M')

    return render_template("dashboard.html", 
                 user=u, 
                 activities=u.activities,
                 rain_proba=rain_proba, 
                 temp=temp,
                 clock_str=dt_str,
                 forecast = forecast_html_str
                 )

#######################################
# http://0.0.0.0:5000/charts/1
#######################################
@app.route('/charts/<int:act_id>', methods=['GET'])
def charts(act_id):
    """Display the chart for the selected activity"""
    
    if "user_id" not in session:
        return redirect('/')
    u = User.query.get(session["user_id"])
    
    current_act = Activity.query.get(act_id)

    # list of event objects belonging to this activity (also to user):
    current_events = current_act.events 
    # print(current_events)
    print(act_id)

    tuples_list = []
    for e in current_events:
        tuples_list.append((e.event_date, e.event_amt))


    def format_data(tup_lst):
        """Combine events for the same date in one date, 
            sort events chronologically"""

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
        # print("Tuples_list_sorted is:", tuples_list_sorted)
        xx = []
        yy = []
        for tup in tuples_list_sorted:
            xx += [ tup[0].strftime("%m/%d/%Y") ]
            yy += [ tup[1] ]
        print(xx, yy)
        return xx,yy

    xx,yy = format_data(tuples_list)


    ########### display by week and month #############

    date_now = datetime.datetime.now().date()
    date7    = date_now - datetime.timedelta(7)
    date30   = date_now - datetime.timedelta(30)

    # loop over events, select only those within last 7 days:
    tup_lst_week = []

    for e in current_events:
        if date7 <= e.event_date.date() <= date_now :
            # print("adding for ", e.event_date.date())
            tup_lst_week.append((e.event_date, e.event_amt))
    # print("tup_lst_week = ", tup_lst_week)

    xx7,yy7 = format_data(tup_lst_week)


    # loop over events, select only those within last 30 days:
    tup_lst_30 = []

    for e in current_events:
        if date30 <= e.event_date.date() <= date_now :
            print("adding for ", e.event_date.date())
            tup_lst_30.append((e.event_date, e.event_amt))
    print("tup_lst_30 = ", tup_lst_30)

    xx30,yy30 = format_data(tup_lst_30)
    

    # now = datetime.datetime.now()
    # example = datetime.datetime(2019, 11, 12)
    # print("Now = ", now, "example = ", example)
    # print("Difference = ", now - example)

    # now = datetime.date.today()
    # dfr = now - ev.event_date
    # dif = dfr.days
        # print(dif)

#   if 0 <= dif <= 7:
#       print("week: ", dif)
#       tup_lst_week.append((e.event_date, e.event_amt))
     

    return render_template("charts.html", 
        user=u,  act=current_act, 
        xx=xx, yy=yy, xx7=xx7, yy7=yy7, xx30=xx30, yy30=yy30)


#######################################
# http://0.0.0.0:5000/delevent/<event_id>
# http://0.0.0.0:5000/delevent/56
#######################################
@app.route('/delevent/<int:event_id>', methods=['GET'])
def delevent(event_id):

    # delete event in database by event_id
    pass

    return  dashboard()





@app.route("/sms", methods=['GET', 'POST'])
def sms_ahoy_reply():
    """Respond to incoming messages with a friendly SMS."""
    # Start our response
    resp = MessagingResponse()

    # Add a message
    resp.message("Ahoy! Thanks so much for your message.")

    return str(resp)





# @app.route('/')

if __name__ == "__main__":

    app.debug = True

    connect_to_db(app)

    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
