"""Seed actlog database."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from model import User, Event, Activity, connect_to_db, db
from server import app
import datetime

# app = Flask(__name__)
# db = SQLAlchemy()

# def connect_to_db(app):
#     """Connect to database."""

#     app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///actlog"
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     db.app = app
#     db.init_app(app)

if __name__ == '__main__':
    connect_to_db(app)

    # Make tables
    db.create_all()

    print("HI INNA")
    print()
    print("You should only run this if you recently")
    print("dropped your database.")
    print()
    print("It will recreate the data you just lost")
    print("(because you dropped your database.)")

    inpt = input("Are you sure you want to continue? (y/n)")

    if inpt == "y":

        # Add initial users and activities:

        # New user, Jane, signs up. Create default activities
        DEFAULT_ACTIVITIES = [
            ("walking", "steps"),
            ("meditation", "minutes"),
            ("pushups", "each"),
            ("class attendance", "yes/no")
        ]
        jane = User(email="jane@jhacks.com", username="jhacks", password="secret")
        for act_name, act_unit in DEFAULT_ACTIVITIES:
            activity = Activity(act_name=act_name, act_unit=act_unit)
            jane.activities.append(activity)

        db.session.add(jane)
        db.session.commit()

        # Jane wants to create her own activity
        jane_painting = Activity(act_name="painting", act_unit="hours")
        jane.activities.append(jane_painting)

        db.session.commit()

        painting_today = Event(event_amt=5,
                               event_date=datetime.datetime.now())
        jane_painting.events.append(painting_today)

        db.session.commit()

        print(User.query.all())
        print(Activity.query.all())
        print(Event.query.all())

