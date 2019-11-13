"""Activity Log"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Activity, Event


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

    # return redirect("/")
    # return redirect(f"/users/{user.user_id}")

# @app.route('/')


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


@app.route('/event', methods=['POST'])
def get_event():

    # Get form variables
    act_id     = request.form.get("activity")
    event_date = request.form.get("date")
    amount     = request.form.get("amount")
    print(f"act_id={act_id}, event_date={event_date}, amount={amount}")
    
    new_event = Event(event_amt=amount, event_date=event_date)

#    user = User.query.get(session["user_id"])

    activity = Activity.query.get(int(act_id))
    print(activity.act_name)
    activity.events.append(new_event)
    db.session.add(new_event)
    db.session.commit()

    flash(f"Event {event_date} {activity.act_name} added")

    return redirect("/event")



# @app.route('/')

if __name__ == "__main__":

    app.debug = True

    connect_to_db(app)

    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
