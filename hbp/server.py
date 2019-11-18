"""Activity Log"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session, jsonify
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

    dct = { "act_id"   : a.act_id,
            "act_name" : a.act_name,
            "act_unit" : a.act_unit }

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

    return render_template("dashboard.html", user=u, activities=u.activities)



#######################################
# http://0.0.0.0:5000/charts/1
#######################################
@app.route('/charts/<int:act_id>', methods=['GET'])
def charts(act_id):
    """Display events by activity"""
    
    if "user_id" not in session:
        return redirect('/')

    u = User.query.get(session["user_id"])
    
    # print(f"user_id={u.user_id}, username={u.username}, email={u.email}")
    # # print(u.activities)  # prints a list of reprs of all activities


    # get all events for act_id
        # a.events
        # a.act_id
    xx = []
    yy = []
    for a in u.activities:
        if (not a.act_id != act_id):
            continue
        # -------------------
        # make list of tuples (date,amt)
        mylist = []
        for e in a.events:
            mylist += [(e.event_date, e.event_amt)] 
        # -------------------
        # sort list of tuples by date
        mylist_sorted = sorted(mylist, key = lambda x: x[0])
        
        for tup in mylist_sorted:
            xx += [ tup[0].strftime("%m/%d/%Y") ]
            yy += [ tup[1] ]

    print(act_id)
    return render_template("charts.html", user=u, xx=xx, yy=yy)


# @app.route('/')

if __name__ == "__main__":

    app.debug = True

    connect_to_db(app)

    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
