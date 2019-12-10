"""Main server file for the Activity Log web app"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Activity, Event

from darksky import forecast

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

import os
import password_hashing

import functions    # my custom functions

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

    # Get login form variables
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

    # flash("Logged in")
    # print("logged in", email)
    return redirect("/dashboard")
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

    # Get registration form variables
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

    act_exists = Activity.query.filter_by(act_name=activity, 
                                          act_unit=unit).first()

    if act_exists:
        flash("Activity already exists")

    if not act_exists:  # add new activity to the database

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
    """Add a new event to the database."""

    # Get event form variables
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

    # flash(f"Event {a.act_name} {event_date} added")

    return redirect("/dashboard")


###########################################
# http://0.0.0.0:5000/api/activity?act_id=1
###########################################
@app.route('/api/activity', methods=['GET'])
def api_activity():
    """Change activity object into a JSON dictionary for AJAX."""
    
    act_id = request.args.get("act_id")

    a = Activity.query.get(int(act_id))

    dct = {"act_id": a.act_id,
           "act_name": a.act_name,
           "act_unit": a.act_unit }

    return jsonify(dct)


@app.route('/api/events', methods=['GET'])
def api_events():
    """Change event object into a JSON dictionary for AJAX."""

    act_id = request.args.get("act_id")

    a = Activity.query.get(int(act_id))
    events = []
    print(a)

    for e in a.events:
        event_dict = {
            "event_date": e.event_date.strftime('%Y-%m-%d'),
            "event_amt": e.event_amt,
            "unit" : e.activity.act_unit
        }
        events.append(event_dict)
        events.sort(key=lambda x: x["event_date"], reverse=True)

    return jsonify(events)


################################
# http://0.0.0.0:5000/dashboard
################################
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Display events by activity."""
    
    if "user_id" not in session:
        return redirect('/')

    u = User.query.get(session["user_id"])
    
    print(f"user_id={u.user_id}, username={u.username}, email={u.email}")
    # print(u.activities)  # prints a list of reprs of all activities

    functions.add_stats_attributes_to_user_activities(u)            

    # San Francisco longitude  and latitude
    lng = -122.4194
    lat = 37.7749

    rain_proba, temp = functions.get_weather(lng, lat)
    forecast_html_str = functions.get_forecast(lng, lat)

    # now_utc = datetime.datetime.now()
    # now_pst = now_utc.astimezone(TZ_PST)
    # dt_str =  now_pst.strftime('%Y-%m-%d %H:%M')

    return render_template("dashboard.html", 
                 user=u, 
                 activities=u.activities,
                 rain_proba=rain_proba, 
                 temp=temp,
                 # clock_str=dt_str,
                 forecast = forecast_html_str
                 )


################################
# http://0.0.0.0:5000/weather
################################
@app.route('/weather', methods=['GET'])
def weather():
    """Display current weather in San Francisco."""           

    # San Francisco longitude  and latitude
    lng = -122.4194
    lat = 37.7749

    rain_proba, temp = functions.get_weather(lng, lat)
    forecast_html_str = functions.get_forecast(lng, lat)


    return render_template("weather.html", 
                 rain_proba=rain_proba, 
                 temp=temp,
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

    # format event tuples into chart data (x for x axis and y for y axis)
    x,y = functions.format_data(tuples_list)

    # display events by last 7 and last 30 days
    x7,y7 = functions.last_n_days(current_events, 7)  
    x30,y30 = functions.last_n_days(current_events, 30) 

    return render_template("charts.html", 
        user=u,  act=current_act, 
        x=x, y=y, x7=x7, y7=y7, x30=x30, y30=y30)


##########################
# http://0.0.0.0:5000/sms
##########################
@app.route("/sms", methods=['GET', 'POST'])
def sms_ahoy_reply():
    """Respond to incoming messages with a friendly SMS."""

    # Start the response
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

    act_summary, act_summary_html = functions.create_act_summary(user)

    client = Client(functions.account_sid, functions.auth_token)

    message = client.messages \
                .create(
                     body=act_summary,
                     from_=functions.my_twilio_number,
                     to=functions.my_mobile_number
                 )

    print(message.sid)
    # flash("SMS with activity summary totals sent!")
    # flash(act_summary)
    mydict = { "mytext": act_summary_html }

    return jsonify(mydict)


###########################################
# http://0.0.0.0:5000/delactivity/<act_id>
# http://0.0.0.0:5000/delactivity/1
###########################################
@app.route('/delactivity/<int:act_id>', methods=['GET'])
def delactivity(act_id):
    """Delete an activity from the database."""    

    myact = Activity.query.get(act_id)
    db.session.delete(myact)
    db.session.commit()

    return redirect("/activity")


###########################################
# http://0.0.0.0:5000/delevent/<event_id>
# http://0.0.0.0:5000/delevent/56
###########################################
@app.route('/delevent/<int:event_id>', methods=['GET'])
def delevent(event_id):
    """Delete an event from the database."""    
 
    ev = Event.query.get(event_id)
    db.session.delete(ev)
    db.session.commit()   

    return redirect("/dashboard")




if __name__ == "__main__":

    app.debug = False

    connect_to_db(app)

    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
