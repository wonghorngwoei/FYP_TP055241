from flask import Blueprint, render_template, flash, request, redirect, url_for, session
from .models import User
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from . import db, mail
import secrets

auth = Blueprint('auth', __name__)

@auth.route('/Login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u_username = request.form.get('username')
        u_password = request.form.get('password')

        user = User.query.filter_by(u_username=u_username).first()
        if user:
            if check_password_hash(user.u_password, u_password):
                flash('Logged in successfully!', category='success')
                # Store user information in the session
                session['u_id'] = user.u_id
                session['username'] = user.u_username
                return redirect(url_for('views.userdashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    
    return render_template("homepage.html")


@auth.route('/Logout', methods=['GET','POST'])
def logout():
    # Clear session data
    session.clear()

    # Redirect the user to the homepage or any other desired page
    return redirect(url_for('views.homepage'))

@auth.route('/Register', methods=['GET','POST'])
def sign_up():
    if request.method == 'POST':
        u_username = request.form.get('u_username')
        u_password= request.form.get('u_password')
        u_fname = request.form.get('u_fname')
        u_lname = request.form.get('u_lname')
        u_email = request.form.get('u_email')
        u_age = request.form.get('u_age')
        u_hpnumber = request.form.get('u_hpnumber')
        u_address = request.form.get('u_address')
        u_gender = request.form.get('u_gender')
        u_usertype = "User"

        # Check if the information already exists
        chk_username = check_username_exists(u_username)
        chk_email = check_email_exists(u_email)

        if chk_username:
           return flash('Username already exists', category='error')
        elif chk_email:
            return flash('Email already exists', category='error')

        newUser = User(u_username=u_username,u_password=generate_password_hash(u_password, method='sha256'),
                       u_fname=u_fname,u_lname=u_lname,u_email=u_email,u_age=u_age,u_hpnumber=u_hpnumber,
                       u_address=u_address,u_gender=u_gender,u_usertype=u_usertype)
        
        db.session.add(newUser)
        db.session.commit()
        flash('Successfully created an account!', 'success')  # Flash success message
        print("Successfully Registered An Account!")
        return redirect(url_for('views.homepage'))

    return render_template("homepage.html")

@auth.route('/ResetPW', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        u_email = request.form.get('u_email')
        user = User.query.filter_by(u_email=u_email).first()
        print(user)
        
        if user:
            # Generate a reset token and set the expiration time
            token = generate_reset_token()
            expiration = datetime.utcnow() + timedelta(hours=1)
            
            # Update the user's reset token and expiration time
            user.reset_token = token
            user.reset_token_expiration = expiration
            db.session.commit()
            
            # Send the password reset email with the token
            send_password_reset_email(user, token)
            flash('If an account with that email address exists, we have sent you an email with instructions to reset your password.')
        
        else:
            flash('User does not exist!')

        return redirect(url_for('views.homepage'))
    
    return render_template('homepage.html')

@auth.route('/reset_password_confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiration < datetime.utcnow():
        flash('Invalid or expired reset token.')
        return redirect(url_for('auth.reset_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            # Update the user's password
            user.u_password = generate_password_hash(password, method='sha256')
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()

            flash('Your password has been successfully reset. You can now log in with your new password.')
            return redirect(url_for('auth.login'))
        else:
            flash('Passwords do not match. Please try again.')
            return redirect(url_for('auth.reset_password_confirm', token=token))

    return render_template('reset_password_confirm.html')

def check_username_exists(u_username):
    # Query the User model to check if the username exists
    user = User.query.filter_by(u_username=u_username).first()

    # If a user object is returned, the username already exists
    return user is not None

def check_email_exists(u_email):
    # Query the User model to check if the username exists
    user = User.query.filter_by(u_email=u_email).first()

    # If a user object is returned, the username already exists
    return user is not None

def generate_reset_token():
    return secrets.token_hex(20)

def send_password_reset_email(user, token):
    # Create the email message
    subject = 'Password Reset Request'
    sender = 'tp055241@mail.apu.edu.my'  # Replace with your email address
    recipient = user.u_email
    message = f'''
    Hi {user.u_username},
    
    You have requested to reset your password. Please click on the following link to reset your password:
    
    {url_for('auth.reset_password_confirm', token=token, _external=True)}
    
    If you did not make this request, please ignore this email.
    
    Best regards,
    Lifestyle Disease Prediction and Management System Team
    '''
    
    # Send the email
    msg = Message(subject, sender=sender, recipients=[recipient])
    msg.body = message
    mail.send_message(msg)