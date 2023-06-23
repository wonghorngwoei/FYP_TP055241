from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime, timedelta

class User(db.Model, UserMixin):
    __tablename__ = 'User'

    u_id = db.Column(db.Integer, primary_key=True)
    u_username = db.Column(db.String(255), unique=True)
    u_password = db.Column(db.String(255))
    u_fname = db.Column(db.String(255))
    u_lname = db.Column(db.String(255))
    u_email = db.Column(db.String(255), unique=True)
    u_age = db.Column(db.String(255))
    u_gender = db.Column(db.String(255))
    u_hpnumber = db.Column(db.String(255))
    u_address = db.Column(db.String(255))
    u_usertype = db.Column(db.String(255))
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    reset_token = db.Column(db.String(150), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)



class Feedback(db.Model):
    __tablename__ = 'Feedback'
    
    f_id = db.Column(db.Integer, primary_key=True)
    f_userID = db.Column(db.Integer, db.ForeignKey('User.u_id'), nullable=False)
    f_feedback = db.Column(db.String(10000))
    f_date = db.Column(db.DateTime(timezone=True), default=func.now())

class Admin(db.Model, UserMixin):
    __tablename__ = 'Admin'

    a_id = db.Column(db.Integer, primary_key=True)
    a_username = db.Column(db.String(255), unique=True)
    a_password = db.Column(db.String(255))
    a_fname = db.Column(db.String(255))
    a_lname = db.Column(db.String(255))
    a_email = db.Column(db.String(255), unique=True)
    a_hpnumber = db.Column(db.String(255))
    a_usertype = db.Column(db.String(255))
    
