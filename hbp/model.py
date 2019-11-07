"""Models and database functions for Activity Log app."""

from flask_sqlalchemy import SQLAlchemy

# This is the connection to the PostgreSQL database; we're getting
# this through the Flask-SQLAlchemy helper library. On this, we can
# find the `session` object, where we do most of our interactions
# (like committing, etc.)

db = SQLAlchemy()


#####################################################################
# Model definitions

class User(db.Model):
    """User of activity log website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True)
    username = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(64), nullable=True, unique=True)
    password = db.Column(db.String(64), nullable=True)
    
    # XXXXXX ?what data type for google account? XXXXXX
    # google_account = db.Column(db.Integer, nullable=True)
    # google_account = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        """Provide helpful representation of user when printed."""

        return f"""<\nUser        user_id={self.user_id} 
            username={self.username}
            email={self.email}>"""


class Activity(db.Model):
    """Movie on ratings website."""

    __tablename__ = "activities"

    act_id = db.Column(db.Integer,
                         autoincrement=True,
                         primary_key=True)
    act_name = db.Column(db.String(30))
    act_unit = db.Column(db.String(15))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    # ?? act_type = db.Column(db.Boolean)


    # Define relationship to user
    user = db.relationship("User",
                           backref=db.backref("activities",
                                              order_by=act_id))
    def __repr__(self):
        """Provide helpful representation of an activity when printed."""

        return f"""<\nActivity    act_id={self.act_id} 
            act_name={self.act_name}
            act_unit={self.act_unit}
            user_id={self.user_id}>"""


class Event(db.Model):
    """Instance (event) of activity by a user."""

    __tablename__ = "events"

    event_id = db.Column(db.Integer,
                          autoincrement=True,
                          primary_key=True)
    act_id = db.Column(db.Integer,
                         db.ForeignKey('activities.act_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    event_amt = db.Column(db.Float)
    event_date = db.Column(db.DateTime) 
    

    # Define relationship to user
    user = db.relationship("User",
                           backref=db.backref("events",
                                              order_by=event_id))

    # Define relationship to activity
    activity = db.relationship("Activity",
                            backref=db.backref("events",
                                               order_by=act_id))

    def __repr__(self):
        """Provide helpful representation of an event of activity when printed."""

        return f"""<\nEvent       event_id={self.event_id}
            act_id={self.act_id}
            user_id={self.user_id}
            event_date={self.event_date}
            event_amt={self.event_amt}>"""


#####################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///actlog'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will
    # leave you in a state of being able to work with the database
    # directly.

    from server import app
    connect_to_db(app)
    print("Connected to DB.")
