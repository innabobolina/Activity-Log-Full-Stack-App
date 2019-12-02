"""Main server file for the Activity Log web app"""

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

# my custom functions
import functions 

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
my_twilio_number = os.environ["MY_TWILIO_NUMBER"]
my_mobile_number = os.environ["MY_MOBILE_NUMBER"]

TZ_PST = tz.gettz("America/Los_Angeles")


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined


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
    events = []
    print(a)

    for e in a.events:
        event_dict = {
            "event_date": e.event_date.strftime('%Y-%m-%d'),
            "event_amt": e.event_amt
        }
        events.append(event_dict)
        events.sort(key=lambda x: x["event_date"])



    return jsonify(events)


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

    functions.add_stats_attributes_to_user_activities(u)            

    # longitude  latitude
    lng = -122.4194
    lat = 37.7749

    rain_proba, temp = functions.get_weather(lng, lat)
    forecast_html_str = functions.get_forecast(lng, lat)

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

    tuples_list = []
    for e in current_events:
        tuples_list.append((e.event_date, e.event_amt))

    x,y = functions.format_data(tuples_list)

    ########### display by week and month #############
    x7,y7 = functions.last_n_days(current_events, 7)  # to display the last week of events
    x30,y30 = functions.last_n_days(current_events, 30) # to display the last month of events

    return render_template("charts.html", 
        user=u,  act=current_act, 
        x=x, y=y, x7=x7, y7=y7, x30=x30, y30=y30)


##########################
# http://0.0.0.0:5000/sms
##########################
@app.route("/sms", methods=['GET', 'POST'])
def sms_ahoy_reply():
    """Respond to incoming messages with a friendly SMS."""

    # Start our response
    resp = MessagingResponse()

    # Add a message
    resp.message("Ahoy! Thanks so much for your message.")

    return str(resp)


################################
# http://0.0.0.0:5000/send_sms
################################
@app.route('/send_sms')
def test_send_sms():
    """Send an SMS to user showing totals per activity for the last 7 days,
    for all activities in the last 7 days.
    """

    user = User.query.get(session["user_id"])
 
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

    client = Client(account_sid, auth_token)

    message = client.messages \
                .create(
                     body=act_summary,
                     from_=my_twilio_number,
                     to=my_mobile_number
                 )

    print(message.sid)

    return redirect("/dashboard")



#######################################
# http://0.0.0.0:5000/delactivity/<act_id>
# http://0.0.0.0:5000/delactivity/1
#######################################
@app.route('/delactivity/<int:act_id>', methods=['GET'])
def delactivity(act_id):

    # delete activity in database by act_id
    

    myact = Activity.query.get(act_id)
    db.session.delete(myact)
    db.session.commit()

    return redirect("/activity")


#######################################
# http://0.0.0.0:5000/delevent/<event_id>
# http://0.0.0.0:5000/delevent/56
#######################################
@app.route('/delevent/<int:event_id>', methods=['GET'])
def delevent(event_id):

    # delete event in database by event_id
 
    ev = Event.query.get(event_id)
    db.session.delete(ev)
    db.session.commit()   


    return redirect("/dashboard")





# @app.route('/')

if __name__ == "__main__":

    app.debug = True

    connect_to_db(app)

    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
