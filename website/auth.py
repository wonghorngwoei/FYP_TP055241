from flask import Blueprint, render_template, flash, request, redirect, url_for, session
from .models import User, Admin
from website import mail
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail
import secrets

auth = Blueprint('auth', __name__)

@auth.route('/Login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(u_username=username).first()
        print(user)
        if user:
            if check_password_hash(user.u_password, password):
                # Display alert message to the user
                alert_message = "Logged in successfully as user: " + username
                flash('Logged in successfully!', category='success')
                # Store user information in the session
                session['u_id'] = user.u_id
                session['username'] = user.u_username
                return redirect(url_for('views.userdashboard', alert_message=alert_message))
                
        admin = Admin.query.filter_by(a_username=username).first()
        print(admin)
        if admin:
            if admin.a_password == password:
                # Display alert message to the user
                alert_message = "Logged in successfully as admin: " + username
                flash('Logged in successfully as admin!', category='success')
                session['a_id'] = admin.a_id
                session['username'] = admin.a_username
                return redirect(url_for('views.admindashboard', alert_message=alert_message))

        alert_message = "Invalid username or password, try again."
        flash('Invalid username or password, try again.', category='error')
        return render_template("homepage.html", alert_message=alert_message)

    return render_template("homepage.html", alert_message=None)


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

def send_mail(user):
    token=user.get_token()
    msg=Message('Password Reset Request', recipients=[user.u_email], sender='noreply@ldpms.com')
    msg.body=f'''
    Hi {user.u_username},
    
    You have requested to reset your password. Please click on the following link to reset your password:
    
    {url_for('auth.reset_token', token=token, _external=True)}
    
    If you did not make this request, please ignore this email.
    
    Best regards,
    Lifestyle Disease Prediction and Management System Team
    '''
    mail.send(msg)

@auth.route('/ResetPW', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        u_email = request.form.get('u_email')
        user = User.query.filter_by(u_email=u_email).first()
        print(user)
        print(u_email)
        
        if user:
            send_mail(user)
            flash('Reset Request Sent. Please Check Your Email.', 'success')
            return redirect(url_for('views.homepage'))
        
    return render_template('homepage.html')


@auth.route('/reset_password_confirm/<token>', methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_token(token)
    
    if user is None:
        flash('Invalid or expired reset token.', 'warning')
        return redirect(url_for('views.homepage'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('u_password')

        if password == confirm_password:
            # Update the user's password
            user.u_password = generate_password_hash(confirm_password, method='sha256')
            db.session.commit()

            flash('Your password has been successfully reset. You can now log in with your new password.')
            return redirect(url_for('views.homepage'))
        else:
            flash('Passwords do not match. Please try again.')
        

    return render_template('confirmResetPW.html')


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


@auth.route('/adminReg', methods=['GET','POST'])
def admin_reg():
    if request.method == 'POST':
        a_username = request.form.get('a_username')
        a_password= request.form.get('a_password')
        a_fname = request.form.get('a_fname')
        a_lname = request.form.get('a_lname')
        a_email = request.form.get('a_email')
        a_hpnumber = request.form.get('a_hpnumber')
        a_usertype = "Admin"

        # Check if the information already exists
        chk_username = check_username_exists(a_username)
        chk_email = check_email_exists(a_email)

        if chk_username:
            flash('Username already exists', category='error')
            return redirect(url_for('views.homepage'))
        elif chk_email:
            flash('Email already exists', category='error')
            return redirect(url_for('views.homepage'))

        newAdmin = Admin(a_username=a_username,a_password=a_password, a_fname=a_fname,a_lname=a_lname,
                         a_email=a_email,a_hpnumber=a_hpnumber,a_usertype=a_usertype)
        
        db.session.add(newAdmin)
        db.session.commit()
        flash('Successfully created an account!', 'success')  # Flash success message
        print("Successfully Registered An Account!")
        return redirect(url_for('views.homepage'))

    return render_template("homepage.html")
