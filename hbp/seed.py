"""Seed actlog database."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import datetime
from sqlalchemy import func

from model import User, Event, Activity, connect_to_db, db
from server import app

# app = Flask(__name__)
# db = SQLAlchemy()


# def connect_to_db(app):
#     """Connect to database."""

#     app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///actlog"
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     db.app = app
#     db.init_app(app)

DEFAULT_ACTIVITIES = [
    ("walking", "steps"),
    ("meditation", "minutes"),
    ("pushups", "each"),
    ("class attendance", "yes/no")
]


if __name__ == '__main__':
    # import os

    # os.system("dropdb actlog")
    # os.system("createdb actlog")

    connect_to_db(app)

    # Make tables
    db.create_all()

    # Add initial users and activities:

    # New user, Jane signs up. Create default activities
    jane = User(email="jane@jhacks.com", username="jhacks", password="secret")
    for act_name, act_unit in DEFAULT_ACTIVITIES:
        activity = Activity(act_name=act_name, act_unit=act_unit)
        jane.activities.append(activity)

    db.session.add(jane)
    db.session.commit()

    # Jane wants to create her own activity
    jane_painting = Activity(act_name="painting", act_unit="hours")
    jane.activities.append(jane_painting)

    db.session.add(jane)
    db.session.commit()

    painting_today = Event(event_amt=5,
                           event_date=datetime.datetime.now())
    jane_painting.append(painting_today)

    db.session.add(jane)
    db.session.commit()



    # Graph all Jane's Painting events



    # walking = Activity(act_name="walking", user=jane, act_unit="steps")

    # ed = User(email="ed@hacks.com", username="edhacks", password="Treo9tz")
    # meditation = Activity(act_name="meditation", act_unit="minutes")

    # # Can add things separately using objects
    # event1 = Event(activity=walking, user=jane, event_amt=9999,
    #         event_date=datetime.datetime(2019, 11, 5))

    db.session.add(event1)

    # Can add using relationships
    walking.events.append(Event(user=jane, event_amt=7777))
    jane.events.append(Event(activity=walking, event_amt=10000))
   
    # ed.activities.append(Event(activity=meditation))

    # # ValueError: Bidirectional attribute conflict detected: 
    # Passing object <Event at 0x7f64ffd28978> to attribute 
    # "User.activities" triggers a modify event on attribute 
    # "User.events" via the backref "Event.user".

    db.session.add(walking)
    db.session.add(jane)
    db.session.add(meditation)

    db.session.add(ed)
    db.session.commit()


    # Test that this worked
    # print(User.query.filter(User.username=='jhacks').one())
    print(User.query.all())
    print(Activity.query.all())
    print(Event.query.all())

    # print(jane, walking, event1)
    # print(session)



