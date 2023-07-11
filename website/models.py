from . import db
from website import app
from flask_login import UserMixin
from itsdangerous import TimedSerializer as Serializer, BadSignature
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
    asthma = db.relationship('Asthma', backref='user', lazy=True)
    diabetes = db.relationship('Diabetes', backref='user', lazy=True)
    stroke = db.relationship('Stroke', backref='user', lazy=True)

    def get_token(self, expires_sec=300):
        expires_at = datetime.utcnow() + timedelta(seconds=expires_sec)
        serializer = Serializer(app.config['SECRET_KEY'])
        token_data = {'u_id': self.u_id, 'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')}
        token = serializer.dumps(token_data)
        return token
    
    @staticmethod
    def verify_token(token):
        serial = Serializer(app.config['SECRET_KEY'])
        try:
            token_data = serial.loads(token)
            user_id = token_data['u_id']
            expires_at = datetime.strptime(token_data['expires_at'], '%Y-%m-%d %H:%M:%S')
            if expires_at < datetime.utcnow():
                return None
            user = User.query.get(user_id)
        except (BadSignature, KeyError):
            return None
        return user


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
    
class Asthma(db.Model):
    __tablename__ = 'Asthma'

    am_id = db.Column(db.Integer, primary_key=True)
    am_userID = db.Column(db.Integer, db.ForeignKey('User.u_id'), nullable=False)
    am_age = db.Column(db.Integer)
    am_sex = db.Column(db.Integer)
    am_sleeping = db.Column(db.Integer)
    am_chesttight = db.Column(db.Integer)
    am_breath = db.Column(db.Integer)
    am_cough = db.Column(db.Integer)
    am_allergy = db.Column(db.Integer)
    am_wheezing = db.Column(db.Integer)
    am_asthma = db.Column(db.Integer)
    am_feedback = db.Column(db.String(10000), nullable=True)
    am_date = db.Column(db.DateTime(timezone=True), default=func.now())
    am_predtarget = db.Column(db.String(20))
    am_refname = db.Column(db.String(255), nullable=True)

class Diabetes(db.Model):
    __tablename__ = 'Diabetes'

    d_id = db.Column(db.Integer, primary_key=True)
    d_userID = db.Column(db.Integer, db.ForeignKey('User.u_id'), nullable=False)
    d_age = db.Column(db.Integer)
    d_highchol = db.Column(db.Integer)
    d_BMI = db.Column(db.Integer)
    d_smoker = db.Column(db.Integer)
    d_heartdisease = db.Column(db.Integer)
    d_physactivity = db.Column(db.Integer)
    d_fruits = db.Column(db.Integer)
    d_veggies = db.Column(db.Integer)
    d_hvyalcoholconsump = db.Column(db.Integer)
    d_genhealth = db.Column(db.Integer)
    d_physhealth = db.Column(db.Integer)
    d_stroke = db.Column(db.Integer)
    d_highbp = db.Column(db.Integer)
    d_diabetes = db.Column(db.Integer)
    d_feedback = db.Column(db.String(10000), nullable=True)
    d_date = db.Column(db.DateTime(timezone=True), default=func.now())
    d_predtarget = db.Column(db.String(20))
    d_refname = db.Column(db.String(255), nullable=True)


class Stroke(db.Model):
    __tablename__ = 'Stroke'

    s_id = db.Column(db.Integer, primary_key=True)
    s_userID = db.Column(db.Integer, db.ForeignKey('User.u_id'), nullable=False)
    s_sex = db.Column(db.Integer)
    s_age = db.Column(db.Integer)
    s_hypertension = db.Column(db.Integer)
    s_heartdisease = db.Column(db.Integer)
    s_married = db.Column(db.Integer)
    s_worktype = db.Column(db.Integer)
    s_avgglucose = db.Column(db.Float)
    s_BMI = db.Column(db.Float)
    s_smoking = db.Column(db.Integer)
    s_stroke = db.Column(db.Integer)
    s_feedback = db.Column(db.String(10000), nullable=True)
    s_date = db.Column(db.DateTime(timezone=True), default=func.now())
    s_predtarget = db.Column(db.String(20))
    s_refname = db.Column(db.String(255), nullable=True)
