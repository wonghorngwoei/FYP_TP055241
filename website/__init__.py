from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tyshnxciauad91asd2ad5wa5'
    #MySQL DB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tp055241@localhost/ldpms'

    db.init_app(app) # Initialize SQLAlchemy with the Flask app
    mail.init_app(app) # Initialize mail with the Flask app

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Feedback

    with app.app_context():
        db.create_all()
    
    return app
