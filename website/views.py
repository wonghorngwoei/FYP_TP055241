from flask import Flask, Blueprint, render_template, redirect, url_for, request, session, flash
from .models import User, Feedback, Admin
from . import db
import requests


views = Blueprint('views', __name__)

@views.route('/')
def homepage():
    return render_template('homepage.html')

@views.route('/userdashboard', methods=['GET','POST'])
def userdashboard():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')

    # Fetch the user's data from the database
    user = User.query.get(userID)
    return render_template('userDashboard.html', user = user, )

@views.route('/admindashboard', methods=['GET','POST'])
def admindashboard():
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')

    users_feedback_data = User.query.join(Feedback).all()
    print(users_feedback_data)

    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)
    return render_template('adminDashboard.html', admin = admin,data=users_feedback_data)

def index():
    active_tab = request.args.get('active_tab', 'home')
    return render_template('userDashboard.html', active_tab=active_tab)

@views.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    api_key = 'AIzaSyDf-tSbLPvre8cFGB5IBGVK3PCwIAHxrJs'
    url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query=hospitals+near+{query}&key={api_key}'

    response = requests.get(url)
    data = response.json()

    # Extract the relevant information from the API response
    results = data['results']
    hospitals = []

    for result in results:
        place_id = result['place_id']
        details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,opening_hours&key={api_key}'
        details_response = requests.get(details_url)
        details_data = details_response.json()

        if 'result' in details_data:
            details_result = details_data['result']
            name = details_result['name']
            address = details_result['formatted_address']
            phone_number = details_result.get('formatted_phone_number', 'N/A')

            if 'opening_hours' in details_result and 'weekday_text' in details_result['opening_hours']:
                opening_hours = details_result['opening_hours']['weekday_text']
                opening_hours_formatted = format_opening_hours(opening_hours)
            else:
                opening_hours_formatted = 'N/A'

            hospitals.append({'name': name, 'address': address, 'phone_number': phone_number, 'opening_hours': opening_hours_formatted})

    return render_template('results.html', hospitals=hospitals)

def format_opening_hours(opening_hours):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    opening_hours_formatted = []

    for day in days:
        for hours in opening_hours:
            if day in hours:
                opening_hours_formatted.append(f'{day}: {hours.split(": ")[1]}')
                break
        else:
            opening_hours_formatted.append(f'{day}: Closed')

    opening_hours_formatted_final = '\n'.join(opening_hours_formatted)
    return opening_hours_formatted_final



# Route for the edit profile page
@views.route('/edit-profile/<int:u_id>', methods=['GET', 'POST'])
def editprofile(u_id):
    user = User.query.get_or_404(u_id)
    if request.method == 'POST':
        # Get the form data
        user.u_fname = request.form['u_fname']
        user.u_lname = request.form['u_lname']
        user.u_age = request.form['u_age']
        user.u_hpnumber = request.form['u_hpnumber']
        user.u_address = request.form['u_address']
        user.u_gender = request.form['u_gender']

        try:
            db.session.commit()
            print("Updated user!")
            return redirect(url_for('views.userdashboard'))
        except:
            return "Error 404: Could not update user"
    
    else:
        return render_template('userDashboard.html', user=user)

# Route for the edit profile page
@views.route('/edit-aprofile/<int:a_id>', methods=['GET', 'POST'])
def editadminprofile(a_id):
    admin = Admin.query.get_or_404(a_id)
    if request.method == 'POST':
        # Get the form data
        admin.a_fname = request.form['a_fname']
        admin.a_lname = request.form['a_lname']
        admin.a_age = request.form['a_age']
        admin.a_hpnumber = request.form['a_hpnumber']
        admin.a_address = request.form['a_address']
        admin.a_gender = request.form['a_gender']

        try:
            db.session.commit()
            print("Updated admin profile!")
            return redirect(url_for('views.admindashboard'))
        except:
            return "Error 404: Could not update admin profile"
    
    else:
        return render_template('adminDashboard.html', admin=admin)
    
@views.route('/Feedback', methods=["POST"])
def feedback():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')

    if request.method == "POST":
        feedback = request.form.get('f_feedback')

        if len(feedback) < 1:
            flash('Note is too short!',category='error')
        else:
            new_feedback = Feedback(f_feedback=feedback, f_userID=userID)
            db.session.add(new_feedback)
            db.session.commit()
            flash('Note added!', category='success')
            return redirect(url_for('views.userdashboard'))
        
    return render_template('userDashboard.html')
