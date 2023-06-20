from flask import Flask, Blueprint, render_template, redirect, url_for, request, session, flash
from .models import User, Feedback
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
    return render_template('userdashboard.html', user = user)

def index():
    active_tab = request.args.get('active_tab', 'home')
    return render_template('userdashboard.html', active_tab=active_tab)

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
        name = result['name']
        address = result['formatted_address']

        # Make a details request for each hospital to get phone numbers and operating hours
        place_id = result['place_id']
        details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}'

        details_response = requests.get(details_url)
        details_data = details_response.json()

        # Extract the phone numbers and operating hours from the details response
        if 'result' in details_data:
            result_details = details_data['result']
            phone_numbers = result_details.get('formatted_phone_number', 'Phone number not available')
            opening_hours = result_details.get('opening_hours', {}).get('weekday_text', [])

            hospitals.append({
                'name': name,
                'address': address,
                'phone_numbers': phone_numbers,
                'opening_hours': opening_hours
            })
        else:
            hospitals.append({
                'name': name,
                'address': address,
                'phone_numbers': 'Phone number not available',
                'opening_hours': []
            })


    # for result in results:
    #     name = result['name']
    #     address = result['formatted_address']
    #     hospitals.append({'name': name, 'address': address})

    return render_template('results.html', hospitals=hospitals)


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
        return render_template('userdashboard.html', user=user)
    
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
        
    return render_template('userdashboard.html')