from flask import Blueprint, render_template, redirect, url_for, request, session, flash, Response
from .models import User, Feedback, Admin, Asthma, Diabetes, Stroke
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from io import StringIO
from sqlalchemy import func
import requests
import pickle
import csv
import numpy as np
import json


views = Blueprint('views', __name__)

# Load the scaler model from the pickle file
with open('notebook/scAsthma.pkl', 'rb') as file:
    scAsthma = pickle.load(file)

# Load the scaler model from the pickle file
with open('notebook/scDiabetes.pkl', 'rb') as file:
    scDiabetes = pickle.load(file)

# Load the scaler model from the pickle file
with open('notebook/qtDiabetes.pkl', 'rb') as file:
    qtDiabetes = pickle.load(file)

# Load the scaler model from the pickle file
with open('notebook/scStroke.pkl', 'rb') as file:
    scStroke = pickle.load(file)

# Load the scaler model from the pickle file
with open('notebook/qtStroke.pkl', 'rb') as file:
    qtStroke = pickle.load(file)

with open('notebook/xgbAsthmaModel.pkl', 'rb') as file:
    asthmaModel = pickle.load(file)

with open('notebook/xgbDiabetesModel.pkl', 'rb') as file:
    diabetesModel = pickle.load(file)

with open('notebook/xgbStrokeModel.pkl', 'rb') as file:
    strokeModel = pickle.load(file)


@views.route('/')
def homepage():
    return render_template('homepage.html')


### User Dashboard Functions ###
@views.route('/userDashboard', methods=['GET','POST'])
def userdashboard():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')

    # Fetch the user's data from the database
    user = User.query.get(userID)

    # Retrieve the counts of diagnosed and not diagnosed asthma cases for the current user's session
    asthma_diagnosed_count = Asthma.query.filter(Asthma.am_predtarget == "myself", Asthma.am_asthma == 1, Asthma.am_userID == user.u_id).count()
    asthma_not_diagnosed_count = Asthma.query.filter(Asthma.am_predtarget == "myself", Asthma.am_asthma == 0, Asthma.am_userID == user.u_id).count()

    # Retrieve the counts of diagnosed and not diagnosed diabetes cases from the database
    diabetes_diagnosed_count = Diabetes.query.filter(Diabetes.d_predtarget == "myself", Diabetes.d_diabetes == 1, Diabetes.d_userID == user.u_id).count()
    diabetes_not_diagnosed_count = Diabetes.query.filter(Diabetes.d_predtarget == "myself", Diabetes.d_diabetes == 0, Diabetes.d_userID == user.u_id).count()

    # Retrieve the counts of diagnosed and not diagnosed stroke cases from the database
    stroke_diagnosed_count = Stroke.query.filter(Stroke.s_predtarget == "myself", Stroke.s_stroke == 1, Stroke.s_userID == user.u_id).count()
    stroke_not_diagnosed_count = Stroke.query.filter(Stroke.s_predtarget == "myself", Stroke.s_stroke == 0, Stroke.s_userID == user.u_id).count()

    
    return render_template('userDashboard.html', user=user, asthma_diagnosed_count=asthma_diagnosed_count, asthma_not_diagnosed_count=asthma_not_diagnosed_count, diabetes_diagnosed_count=diabetes_diagnosed_count, 
                            diabetes_not_diagnosed_count=diabetes_not_diagnosed_count, stroke_diagnosed_count=stroke_diagnosed_count, stroke_not_diagnosed_count=stroke_not_diagnosed_count)
def index():
    active_tab = request.args.get('active_tab', 'home')
    return render_template('userDashboard.html', active_tab=active_tab)

@views.route('/change-u_password/<int:u_id>', methods=['POST'])
def user_change_password(u_id):
    # Retrieve the user from the database
    user = User.query.get(u_id)

    # Get the input values from the form
    current_password = request.form.get('u_password')
    new_password = request.form.get('u_newPW')
    confirm_password = request.form.get('u_newPWconfirmed')

    # Check if the current password matches the stored password hash
    if check_password_hash(user.u_password, current_password):
        # Check if the new password and confirm password match
        if new_password == confirm_password:
            # Generate a new password hash
            new_password_hash = generate_password_hash(new_password)

            # Update the user's password in the database
            user.u_password = new_password_hash
            db.session.commit()

            # Password successfully changed
            flash('Password has been changed successfully.', 'success')
        else:
            # New password and confirm password do not match
            flash('New password and confirm password do not match.', 'error')
    else:
        # Current password is incorrect
        flash('Incorrect current password.', 'error')

    # Redirect to the user profile page
    return redirect(url_for('views.userdashboard', user=user))

# Find Nearby Hospital (User)
@views.route('/findNearbyHospital', methods=['GET','POST'])
def findNearbyHospital():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('findNearbyHospital.html', user = user)


@views.route('/search', methods=['POST'])
def search():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Fetch the user's data from the database
    user = User.query.get(userID)
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

    return render_template('findNearbyHospital.html', hospitals=hospitals, user = user)

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
def editProfile(u_id):
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
            flash("Updated user profile!")
            return redirect(url_for('views.userdashboard'))
        except:
            flash("Error 404: Could not update user")
            return redirect(url_for('views.userdashboard'))
    
    else:
        return render_template('userDashboard.html', user=user)
    
##### User Past Prediction Record #####
@views.route('/pastPredictionRecords', methods=['GET'])
def pastPredictionRecords():
     # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Fetch the data for each report
    asthma_records = User.query.join(Asthma).all()
    diabetes_records = User.query.join(Diabetes).all()
    stroke_records = User.query.join(Stroke).all()

    # Fetch the user's data from the database
    user = User.query.get(userID)
    return render_template('pastPredictionRecords.html', user=user, asthma_records=asthma_records, diabetes_records=diabetes_records, stroke_records=stroke_records)


##### User Feedback #####
@views.route('/FeedbackForm', methods=['GET','POST'])
def feedbackForm():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')

    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('userfeedback.html', user=user)
    
@views.route('/Feedback', methods=["POST"])
def feedback():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')

    if request.method == "POST":
        feedback = request.form.get('f_feedback')

        if len(feedback) < 1:
            flash('Feedback is too short!',category='error')
        else:
            new_feedback = Feedback(f_feedback=feedback, f_userID=userID)
            db.session.add(new_feedback)
            db.session.commit()
            flash('Feedback submitted!', category='success')
            return redirect(url_for('views.userdashboard'))
        
    return render_template('userDashboard.html')


##### Admin Dashboard Functions #####
@views.route('/admindashboard', methods=['GET','POST'])
def admindashboard():
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')
    total_users = User.query.count()
    asthma_count = Asthma.query.count()
    diabetes_count = Diabetes.query.count()
    stroke_count = Stroke.query.count()
    feedback_count = Feedback.query.count()
    recent_users = User.query.order_by(User.u_id.desc()).limit(15).all()

    total_predictions_count = asthma_count + diabetes_count + stroke_count

    # Retrieve the diabetes age group data from your data source
    age_group_counts = [0] * 13

    # Query the database to get the counts for each age group
    diabetes_records = Diabetes.query.all()
    for record in diabetes_records:
        age_group = record.d_age
        age_group_counts[age_group - 1] += 1

    # Retrieve the counts of predicted diabetes cases for different BMI categories
    underweight_cases = Diabetes.query.filter(Diabetes.d_BMI < 18.5).count()
    normal_weight_cases = Diabetes.query.filter(Diabetes.d_BMI >= 18.5, Diabetes.d_BMI < 25).count()
    overweight_cases = Diabetes.query.filter(Diabetes.d_BMI >= 25, Diabetes.d_BMI < 30).count()
    obese_cases = Diabetes.query.filter(Diabetes.d_BMI >= 30).count()

    # Retrieve the data for High Cholesterol Status from your data source
    with_cholesterol_cases = Diabetes.query.filter_by(d_highchol=1).count()
    without_cholesterol_cases = Diabetes.query.filter_by(d_highchol=0).count()

    # Retrieve the data for the chart
    with_highbp_count = Diabetes.query.filter_by(d_highbp=1).count()
    without_highbp_count = Diabetes.query.filter_by(d_highbp=0).count()

    # Calculate the percentages
    total_cases = with_highbp_count + without_highbp_count
    with_highbp_percentage = round((with_highbp_count / total_cases) * 100, 2)
    without_highbp_percentage = round((without_highbp_count / total_cases) * 100, 2)

    # Fetch the data for common symptoms from the Asthma table
    asthma_records = Asthma.query.all()
    chest_tightness_cases = sum(record.am_chesttight for record in asthma_records if record.am_asthma == 1)
    shortness_of_breath_cases = sum(record.am_breath for record in asthma_records if record.am_asthma == 1)
    coughing_cases = sum(record.am_cough for record in asthma_records if record.am_asthma == 1)
    allergy_cases = sum(record.am_allergy for record in asthma_records if record.am_asthma == 1)
    wheezing_cases = sum(record.am_wheezing for record in asthma_records if record.am_asthma == 1)
    sleeping_cases = sum(record.am_sleeping for record in asthma_records if record.am_asthma == 1)

    age_groups = ['0-17', '18-30', '31-45', '46-60', '61+']

    asthma_cases = []
    non_asthma_cases = []

    for age_group in age_groups:
        asthma_group_cases = filter_asthma_cases_by_age_group(age_group, asthma=True)
        non_asthma_group_cases = filter_asthma_cases_by_age_group(age_group, asthma=False)
        
        asthma_cases.append(asthma_group_cases)
        non_asthma_cases.append(non_asthma_group_cases)

    # Filter the asthma records by gender and prediction for Asthma
    am_male_records_yes = [record for record in asthma_records if record.am_sex == 1 and record.am_asthma == 1]
    am_male_records_no = [record for record in asthma_records if record.am_sex == 1 and record.am_asthma == 0]
    am_female_records_yes = [record for record in asthma_records if record.am_sex == 0 and record.am_asthma == 1]
    am_female_records_no = [record for record in asthma_records if record.am_sex == 0 and record.am_asthma == 0]

    # Count the number of asthma cases for each gender and prediction category
    am_male_cases_yes = len(am_male_records_yes)
    am_male_cases_no = len(am_male_records_no)
    am_female_cases_yes = len(am_female_records_yes)
    am_female_cases_no = len(am_female_records_no)

    # Load the data from the database
    stroke_records = Stroke.query.all()

    # Filter the stroke records by work type
    work_type_counts = {
        'Never Worked': 0,
        'Children': 0,
        'Govt Job': 0,
        'Self-employed': 0,
        'Private': 0
    }

    for record in stroke_records:
        work_type = record.s_worktype
        if work_type == 0:
            work_type_counts['Never Worked'] += 1
        elif work_type == 1:
            work_type_counts['Children'] += 1
        elif work_type == 2:
            work_type_counts['Govt Job'] += 1
        elif work_type == 3:
            work_type_counts['Self-employed'] += 1
        elif work_type == 4:
            work_type_counts['Private'] += 1

    # Calculate the percentage of stroke cases for each work type
    total_cases = len(stroke_records)
    work_type_percentages = {
        work_type: (count / total_cases) * 100 for work_type, count in work_type_counts.items()
    }

    # Convert the percentages to a JSON format
    work_type_percentages_json = json.dumps(list(work_type_percentages.values()))

    stroke_cases_yes = [0] * len(age_groups)
    stroke_cases_no = [0] * len(age_groups)

    # Filter the stroke records and count the cases for each age group
    for record in stroke_records:
        age = record.s_age
        stroke_prediction = record.s_stroke

        # Group the records into age groups
        if age <= 30:
            age_group_index = 0
        elif age <= 45:
            age_group_index = 1
        elif age <= 60:
            age_group_index = 2
        else:
            age_group_index = 3

        # Increment the corresponding stroke cases count based on stroke prediction
        if stroke_prediction == 1:
            stroke_cases_yes[age_group_index] += 1
        else:
            stroke_cases_no[age_group_index] += 1

    # Retrieve the counts of predicted stroke cases for different BMI categories
    s_underweight_cases_t = Stroke.query.filter(Stroke.s_BMI < 18.5, Stroke.s_stroke == 1).count()
    s_normal_weight_cases_t = Stroke.query.filter(Stroke.s_BMI >= 18.5, Stroke.s_BMI < 25, Stroke.s_stroke == 1).count()
    s_overweight_cases_t = Stroke.query.filter(Stroke.s_BMI >= 25, Stroke.s_BMI < 30, Stroke.s_stroke == 1).count()
    s_obese_cases_t = Stroke.query.filter(Stroke.s_BMI >= 30, Stroke.s_stroke == 1).count()

    # Retrieve the counts of predicted stroke cases for different BMI categories
    s_underweight_cases_f = Stroke.query.filter(Stroke.s_BMI < 18.5, Stroke.s_stroke == 0).count()
    s_normal_weight_cases_f = Stroke.query.filter(Stroke.s_BMI >= 18.5, Stroke.s_BMI < 25, Stroke.s_stroke == 0).count()
    s_overweight_cases_f = Stroke.query.filter(Stroke.s_BMI >= 25, Stroke.s_BMI < 30, Stroke.s_stroke == 0).count()
    s_obese_cases_f = Stroke.query.filter(Stroke.s_BMI >= 30, Stroke.s_stroke == 0).count()

    # Retrieve the data for the time periods and average glucose levels
    query = db.session.query(func.date_format(Stroke.s_date, '%Y-%m').label('time_period'),
                             func.avg(Stroke.s_avgglucose).label('average_glucose')) \
                      .filter(Stroke.s_stroke == 1) \
                      .group_by('time_period') \
                      .order_by('time_period')

    results = query.all()

    time_periods = [result.time_period for result in results]
    average_glucose_levels = [result.average_glucose for result in results]

    # Serialize the data to JSON
    time_periods_json = json.dumps(time_periods)
    average_glucose_levels_json = json.dumps(average_glucose_levels)



    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)
    return render_template('adminDashboard.html', admin=admin, total_users=total_users, 
                           total_predictions_count=total_predictions_count, asthma_count=asthma_count, 
                           diabetes_count=diabetes_count, stroke_count=stroke_count, feedback_count=feedback_count, 
                           recent_users=recent_users, age_group_counts=age_group_counts, underweight_cases=underweight_cases, normal_weight_cases=normal_weight_cases, 
                           overweight_cases=overweight_cases, obese_cases=obese_cases, with_cholesterol_cases=with_cholesterol_cases, without_cholesterol_cases=without_cholesterol_cases, 
                           with_highbp_percentage=with_highbp_percentage, without_highbp_percentage=without_highbp_percentage, chest_tightness_cases=chest_tightness_cases,
                           shortness_of_breath_cases=shortness_of_breath_cases, coughing_cases=coughing_cases, allergy_cases=allergy_cases, wheezing_cases=wheezing_cases, sleeping_cases=sleeping_cases, 
                           asthma_cases=asthma_cases, non_asthma_cases=non_asthma_cases, am_male_cases_yes=am_male_cases_yes, am_male_cases_no=am_male_cases_no, am_female_cases_yes=am_female_cases_yes, 
                           am_female_cases_no=am_female_cases_no, work_type_percentages=work_type_percentages_json, stroke_cases_yes=stroke_cases_yes, stroke_cases_no=stroke_cases_no,
                           s_underweight_cases_t=s_underweight_cases_t, s_normal_weight_cases_t=s_normal_weight_cases_t, s_overweight_cases_t=s_overweight_cases_t, s_obese_cases_t=s_obese_cases_t,
                           s_underweight_cases_f=s_underweight_cases_f, s_normal_weight_cases_f=s_normal_weight_cases_f, s_overweight_cases_f=s_overweight_cases_f, s_obese_cases_f=s_obese_cases_f,
                           time_periods_json=time_periods_json, average_glucose_levels_json=average_glucose_levels_json)

def filter_asthma_cases_by_age_group(age_group, asthma=True):
    if age_group == '0-17':
        if asthma:
            return Asthma.query.filter(Asthma.am_age <= 17, Asthma.am_asthma == 1).count()
        else:
            return Asthma.query.filter(Asthma.am_age <= 17, Asthma.am_asthma == 0).count()
    elif age_group == '18-30':
        if asthma:
            return Asthma.query.filter(Asthma.am_age >= 18, Asthma.am_age <= 30, Asthma.am_asthma == 1).count()
        else:
            return Asthma.query.filter(Asthma.am_age >= 18, Asthma.am_age <= 30, Asthma.am_asthma == 0).count()
    elif age_group == '31-45':
        if asthma:
            return Asthma.query.filter(Asthma.am_age >= 31, Asthma.am_age <= 45, Asthma.am_asthma == 1).count()
        else:
            return Asthma.query.filter(Asthma.am_age >= 31, Asthma.am_age <= 45, Asthma.am_asthma == 0).count()
    elif age_group == '46-60':
        if asthma:
            return Asthma.query.filter(Asthma.am_age >= 46, Asthma.am_age <= 60, Asthma.am_asthma == 1).count()
        else:
            return Asthma.query.filter(Asthma.am_age >= 46, Asthma.am_age <= 60, Asthma.am_asthma == 0).count()
    elif age_group == '61+':
        if asthma:
            return Asthma.query.filter(Asthma.am_age >= 61, Asthma.am_asthma == 1).count()
        else:
            return Asthma.query.filter(Asthma.am_age >= 61, Asthma.am_asthma == 0).count()
    else:
        return 0
# Route for the edit profile page
@views.route('/edit-aprofile/<int:a_id>', methods=['GET', 'POST'])
def editAdminProfile(a_id):
    admin = Admin.query.get_or_404(a_id)
    if request.method == 'POST':
        # Get the form data
        admin.a_fname = request.form['a_fname']
        admin.a_lname = request.form['a_lname']
        admin.a_hpnumber = request.form['a_hpnumber']

        try:
            db.session.commit()
            flash("Updated admin profile!")
            return redirect(url_for('views.admindashboard'))
        except:
            flash("Error 404: Could not update admin profile")
            return redirect(url_for('views.admindashboard'))
    
    else:
        return render_template('adminDashboard.html', admin=admin)
    
@views.route('/change-password/<int:a_id>', methods=['POST'])
def change_password(a_id):
    # Retrieve the a from the database
    admin = Admin.query.get(a_id)

    # Get the input values from the form
    current_password = request.form.get('a_password')
    new_password = request.form.get('a_newPW')
    confirm_password = request.form.get('a_newPWconfirmed')

    # Check if the current password matches the stored password hash
    if admin.a_password == current_password:
        # Check if the new password and confirm password match
        if new_password == confirm_password:

            # Update the admin's password in the database
            admin.a_password = new_password
            db.session.commit()

            # Password successfully changed
            flash('Password has been changed successfully.', 'success')
        else:
            # New password and confirm password do not match
            flash('New password and confirm password do not match.', 'error')
    else:
        # Current password is incorrect
        flash('Incorrect current password.', 'error')

    # Redirect to the admin profile page
    return redirect(url_for('views.admindashboard', admin=admin))
    
# Manage User Account (Admin)
@views.route('/manageUserAccount', methods=['GET','POST'])
def getUserInfo():
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')

    # Fetch the user's data from the database
    user = User.query.all()
    print(user)

    # Assuming you have models for Asthma, Diabetes, and Stroke predictions
    asthma_predictions = [prediction.am_userID for prediction in Asthma.query.all()]
    diabetes_predictions = [prediction.d_userID for prediction in Diabetes.query.all()]
    stroke_predictions = [prediction.s_userID for prediction in Stroke.query.all()]

    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)

    # Get the flash message from the session
    messages = session.pop('flash_messages', [])

    return render_template('manageUserAccount.html', admin = admin, user=user, asthma_predictions=asthma_predictions, diabetes_predictions=diabetes_predictions, stroke_predictions=stroke_predictions, messages=messages)

@views.route('/delete_user/<int:u_id>', methods=['GET', 'POST'])
def deleteUser(u_id):
    # Retrieve the user from the database based on the user_id
    userdel = User.query.get_or_404(u_id)

    try:
        # Delete the user from the database
        db.session.delete(userdel)
        db.session.commit()
        flash("User Deleted Successully.")
    except:
        flash("Problem deleting the user account.")
        # Redirect to the user account page or any other desired page

    # Store the flash message in the session
    session['flash_messages'] = [message for message in session.get('flashes', [])]

    # Redirect to the user account page or any other desired page
    return redirect(url_for('views.getUserInfo'))


# Route for the edit profile page
@views.route('/edit_user/<int:u_id>', methods=['GET', 'POST'])
def editUser(u_id):
    # Retrieve the user from the database based on the user_id
    user = User.query.get_or_404(u_id)

    if request.method == 'POST':
        # Update the user's information based on the form data
        try:
            user.u_fname = request.form['u_fname']
            user.u_lname = request.form['u_lname']
            user.u_email = request.form['u_email']
            user.u_age = request.form['u_age']
            user.u_gender = request.form['u_gender']
            user.u_hpnumber = request.form['u_hpnumber']
            user.u_address = request.form['u_address']

            # Save the changes to the database
            db.session.commit()
            flash('Successfully updated selected user profile.')
            # Redirect to the user account page or any other desired page
            return redirect(url_for('views.getUserInfo'))

        except:
            flash('There was an error updating your profile.')
            return render_template('manageUserAccount.html', user=user)
        
    # Store the flash message in the session
    session['flash_messages'] = [message for message in session.get('flashes', [])]

    # Render the edit user form with the pre-filled user information
    return render_template('manageUserAccount.html', user=user)

#View Prediction Report (Admin)
@views.route('/viewReports', methods=['GET'])
def viewPredictionReports():
     # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')
    # Fetch the data for each report
    asthma_reports = User.query.join(Asthma).all()
    diabetes_reports = User.query.join(Diabetes).all()
    stroke_reports = User.query.join(Stroke).all()

    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)
    return render_template('viewPredictionReport.html', admin=admin, asthma_reports=asthma_reports, diabetes_reports=diabetes_reports, stroke_reports=stroke_reports)


# View Feedback (Admin)
@views.route('/viewFeedback', methods=['GET'])
def getUserFeedback():
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')

    users_feedback_data = User.query.join(Feedback).all()
    print(users_feedback_data)

    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)
    return render_template('viewFeedback.html', admin = admin,data=users_feedback_data)

# Export Feedback CSV
@views.route('/exportFeedback', methods=['GET'])
def exportFeedback():
    # Get feedback data from the database
    feedback_data = User.query.join(Feedback).all()

    # Create a CSV string
    csv_data = create_csv(feedback_data)

    # Create a response with the CSV data
    response = Response(csv_data, mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='feedback.csv')

    return response

def create_csv(feedback_data):
    # Create a file-like object in memory
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)

    # Write the header row
    csv_writer.writerow(['User First Name', 'User Last Name', 'User Email', 'User Phone Number', 'Feedback ID', 'Feedback User ID', 'Feedback', 'Date'])

    # Write the feedback data rows
    for user in feedback_data:
        for feedback in user.feedbacks:
            csv_writer.writerow([user.u_fname, user.u_lname, user.u_email, user.u_hpnumber, feedback.f_id, feedback.f_userID, feedback.f_feedback, feedback.f_date])

    # Get the CSV data as a string
    csv_data.seek(0)
    csv_string = csv_data.getvalue()

    return csv_string


##### Asthma Prediction #####
@views.route('/asthmaPredictionForm' , methods=['GET','POST'])
def asthmaPredictionForm():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')

    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('asthmaprediction.html', user=user)

@views.route('/asthmaPrediction', methods=['GET','POST'])
def predictAsthma():
    if request.method == 'POST':
        # Retrieve input from the request
        age = request.form['age']
        sex = request.form['sex']
        sleeping = request.form['sleeping']
        chesttight = request.form['chesttight']
        breath = request.form['breath']
        cough = request.form['cough']
        allergy = request.form['allergy']
        wheezing = request.form['wheezing']
        predTarget = request.form['predictionTarget']
        refName = request.form['referenceName'] if predTarget == 'Others' else None

        form_array = np.array([[age, sex, sleeping, breath, chesttight, cough, allergy, wheezing]]).astype(int)
        print(form_array)
        sc_a = scAsthma.transform(form_array)
        prediction = asthmaModel.predict(sc_a)[0]
        prediction_percentage_true = asthmaModel.predict_proba(sc_a)[0,1]
        print(prediction)
         # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Create a new Asthma object
        asthma = Asthma(
            am_userID=userID,
            am_age=int(age),
            am_sex=int(sex),
            am_sleeping=int(sleeping),
            am_chesttight=int(chesttight),
            am_breath=int(breath),
            am_cough=int(cough),
            am_allergy=int(allergy),
            am_wheezing=int(wheezing),
            am_asthma=int(prediction),
            am_feedback=None,  # Initialize feedback as None
            am_predtarget=predTarget,
            am_refname=refName
        )
        # Add the Asthma object to the database session
        db.session.add(asthma)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.asthmaResult', user=user, age=age, sex=sex, sleeping=sleeping, chesttight=chesttight, breath=breath, cough=cough, allergy=allergy, wheezing=wheezing, prediction=prediction, prediction_percentage_true=prediction_percentage_true))
        
    return redirect(url_for('views.userdashboard'))

@views.route('/asthmaResult' , methods=['GET','POST'])
def asthmaResult():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
    age=request.args.get('age')
    sex=request.args.get('sex')
    sleeping=request.args.get('sleeping')
    chesttight=request.args.get('chesttight')
    breath=request.args.get('breath')
    cough=request.args.get('cough')
    allergy=request.args.get('allergy')
    wheezing=request.args.get('wheezing')

    prediction = request.args.get('prediction')
    

    prediction_percentage_true = float(request.args.get('prediction_percentage_true'))

    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('asthmaResult.html', user=user, age=int(age), sex=int(sex), sleeping=int(sleeping), chesttight=int(chesttight), breath=int(breath), cough=int(cough), allergy=int(allergy), wheezing=int(wheezing), prediction=int(prediction), prediction_percentage_true=prediction_percentage_true)

@views.route('/asthmaResultFeedback' , methods=['GET','POST'])
def asthmaResultFeedback():
    if request.method == 'POST':
        # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')
        
        # Retrieve the feedback from the form
        feedback = request.form['am_feedback']

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Retrieve the latest Asthma record for the user
        asthma = Asthma.query.filter_by(am_userID=userID).order_by(Asthma.am_id.desc()).first()


        # Update the Asthma record with the user's feedback
        try:
            # Update the Asthma record with the user's feedback
            asthma.am_feedback = feedback
            # Commit the changes to the database
            db.session.commit()
        except Exception as e:
            print(e)
            flash("Failed to submit asthma prediction feedback, please try again.")
        else:
            flash("Successfully submitted asthma prediction feedback.")
       
        return redirect(url_for('views.userdashboard', user=user))  # Redirect to user dashboard after submitting feedback

    return render_template('userDashboard.html')

# Export Asthma CSV
@views.route('/exportAsthma', methods=['GET'])
def exportAsthma():
    # Get feedback data from the database
    asthma_data = Asthma.query.all()

    # Create a CSV string
    csv_asthma = create_asthma_csv(asthma_data)

    # Create a response with the CSV data
    response = Response(csv_asthma, mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='asthma.csv')

    return response

def create_asthma_csv(asthma_data):
    # Create a file-like object in memory
    csv_asthma = StringIO()
    csv_AsthmaWriter = csv.writer(csv_asthma)

    # Write the header row
    csv_AsthmaWriter.writerow(['am_id', 'am_userID', 'am_sex', 'am_age', 'am_sleeping', 'am_chesttight', 'am_breath', 
                         'am_cough', 'am_allergy', 'am_wheezing', 'am_asthma', 'am_feedback', 'am_date'])
    
    # Write the asthma data rows
    for asthma in asthma_data:
        csv_AsthmaWriter.writerow([asthma.am_id, asthma.am_userID, asthma.am_sex, asthma.am_age, asthma.am_sleeping, asthma.am_chesttight, asthma.am_breath, 
                             asthma.am_cough, asthma.am_allergy, asthma.am_wheezing, asthma.am_asthma, asthma.am_feedback, asthma.am_date])

    # Get the CSV data as a string
    csv_asthma.seek(0)
    csv_asthmaString = csv_asthma.getvalue()

    return csv_asthmaString

##### Diabetes Prediction #####
@views.route('/diabetesPredictionForm' , methods=['GET','POST'])
def diabetesPredictionForm():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # # Retrieve the result from the query parameter
    # result = request.args.get('result')

    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('diabetesprediction.html', user=user)

@views.route('/diabetesPrediction', methods=['GET','POST'])
def predictDiabetes():
    if request.method == 'POST':
        # Retrieve input from the request
        getAge = int(request.form['age'])

        if getAge >= 18 and getAge <= 24:
            age = 1
        elif getAge >= 25 and getAge <= 29:
            age = 2
        elif getAge >= 30 and getAge <= 34:
            age = 3
        elif getAge >= 35 and getAge <= 39:
            age = 4
        elif getAge >= 40 and getAge <= 44:
            age = 5
        elif getAge >= 45 and getAge <= 49:
            age = 6
        elif getAge >= 50 and getAge <= 54:
            age = 7
        elif getAge >= 55 and getAge <= 59:
            age = 8
        elif getAge >= 60 and getAge <= 64:
            age = 9
        elif getAge >= 65 and getAge <= 69:
            age = 10
        elif getAge >= 70 and getAge <= 74:
            age = 11
        elif getAge >= 75 and getAge <= 79:
            age = 12
        else:
            age = 13

        highChol = request.form['highChol']  
        bmi = request.form['bmi']
        smoker = request.form['smoker']
        heartdisease = request.form['heartdisease']
        physactivity = request.form['physactivity']
        fruits = request.form['fruits']
        veggies = request.form['veggies']
        hvyalcoholconsump = request.form['hvyalcoholconsump']
        generalHealth = request.form['generalHealth']
        physicalHealth = request.form['physicalHealth']
        stroke = request.form['stroke']
        highBP = request.form['highBP']
        predTarget = request.form['predictionTarget']
        refName = request.form['referenceName'] if predTarget == 'Others' else None


        form_array = np.array([[age, highChol, bmi, smoker, heartdisease, physactivity, fruits, veggies, 
                                hvyalcoholconsump, generalHealth, physicalHealth, stroke, highBP]]).astype(int)
        print(form_array)
        sc_d = scDiabetes.transform(form_array)

        sc_d[0][2] = qtDiabetes[0].transform(sc_d[0][2].reshape(-1,1))
        sc_d[0][10] = qtDiabetes[1].transform(sc_d[0][10].reshape(-1,1))
        prediction = diabetesModel.predict(sc_d)[0]
        prediction_percentage_true = diabetesModel.predict_proba(sc_d)[0,1]
        print(prediction)
         # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Create a new Diabetes object
        diabetes = Diabetes(
            d_userID = userID,
            d_age = int(age),
            d_highchol = int(highChol),
            d_BMI = int(bmi),
            d_smoker = int(smoker),
            d_heartdisease = int(heartdisease),
            d_physactivity = int(physactivity),
            d_fruits = int(fruits),
            d_veggies = int(veggies),
            d_hvyalcoholconsump = int(hvyalcoholconsump),
            d_genhealth = int(generalHealth),
            d_physhealth = int(physicalHealth),
            d_stroke = int(stroke),
            d_highbp = int(highBP),
            d_diabetes = int(prediction),
            d_feedback = None,  # feedback as None as it will be updated by the user input after prediction result is out.
            d_predtarget=predTarget,
            d_refname=refName
        )
        # Add the Diabetes object to the database session
        db.session.add(diabetes)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.diabetesResult', user=user, getAge=getAge, highChol=highChol, bmi=bmi, smoker=smoker, heartdisease=heartdisease, physactivity=physactivity, fruits=fruits, veggies=veggies, hvyalcoholconsump=hvyalcoholconsump, 
                                generalHealth=generalHealth, physicalHealth=physicalHealth, stroke=stroke, highBP=highBP, prediction=prediction, diabetes=diabetes, prediction_percentage_true=prediction_percentage_true))
        
    return redirect(url_for('views.userdashboard'))

@views.route('/diabetesResult' , methods=['GET','POST'])
def diabetesResult():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
    getAge = request.args.get('getAge')
    highChol = request.args.get('highChol')
    bmi = request.args.get('bmi')
    smoker = request.args.get('smoker')
    heartdisease = request.args.get('heartdisease')
    physactivity = request.args.get('physactivity')
    fruits = request.args.get('fruits')
    veggies = request.args.get('veggies')
    hvyalcoholconsump = request.args.get('hvyalcoholconsump')
    generalHealth = request.args.get('generalHealth')
    physicalHealth = request.args.get('physicalHealth')
    stroke = request.args.get('stroke')
    highBP = request.args.get('highBP')

    prediction = request.args.get('prediction')

    prediction_percentage_true = float(request.args.get('prediction_percentage_true'))
    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('diabetesResult.html', user=user, prediction=int(prediction), prediction_percentage_true=prediction_percentage_true)

@views.route('/DiabetesResultFeedback' , methods=['GET','POST'])
def diabetesResultFeedback():
    if request.method == 'POST':
        # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')
        
        # Retrieve the feedback from the form
        feedback = request.form['d_feedback']

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Retrieve the latest Diabetes record for the user
        diabetes = Diabetes.query.filter_by(d_userID=userID).order_by(Diabetes.d_id.desc()).first()
        
        # Update the Diabetes record with the user's feedback
        try:
            diabetes.d_feedback = feedback
            db.session.commit()
        except Exception as e:
            print(e)
            flash("Failed to submit diabetes prediction feedback, please try again.")
        else:
            flash("Successfully submitted diabetes prediction feedback.")

        return redirect(url_for('views.userdashboard', user=user))

    return render_template('userDashboard.html')

# Export Diabetes CSV
@views.route('/exportDiabetes', methods=['GET'])
def exportDiabetes():
    # Get feedback data from the database
    diabetes_data = Diabetes.query.all()

    # Create a CSV string
    csv_diabetes = create_diabetes_csv(diabetes_data)

    # Create a response with the CSV data
    response = Response(csv_diabetes, mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='diabetes.csv')

    return response

def create_diabetes_csv(diabetes_data):
    # Create a file-like object in memory
    csv_diabetes = StringIO()
    csv_DiabetesWriter = csv.writer(csv_diabetes)

    # Write the header row
    csv_DiabetesWriter.writerow(['d_id', 'd_userID', 'd_age', 'd_highchol', 'd_BMI', 'd_smoker', 'd_heartdisease', 'd_physactivity', 'd_fruits', 'd_veggies', 
                         'd_hvyalcoholconsump', 'd_genhealth', 'd_physhealth', 'd_stroke', 'd_highbp', 'd_diabetes', 'd_feedback', 'd_date'])
    
    # Write the diabetes data rows
    for diabetes in diabetes_data:
        csv_DiabetesWriter.writerow([diabetes.d_id, diabetes.d_userID, diabetes.d_age, diabetes.d_highchol, diabetes.d_BMI, diabetes.d_smoker, diabetes.d_heartdisease, diabetes.d_physactivity, diabetes.d_fruits, diabetes.d_veggies, 
                             diabetes.d_hvyalcoholconsump, diabetes.d_genhealth, diabetes.d_physhealth, diabetes.d_stroke, diabetes.d_highbp, diabetes.d_diabetes, diabetes.d_feedback, diabetes.d_date])

    # Get the CSV data as a string
    csv_diabetes.seek(0)
    csv_diabetesString = csv_diabetes.getvalue()

    return csv_diabetesString

##### Stroke Prediction #####
@views.route('/strokePredictionForm' , methods=['GET','POST'])
def strokePredictionForm():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
    # result = request.args.get('result')

    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('strokeprediction.html', user=user)

@views.route('/strokePrediction', methods=['GET','POST'])
def predictStroke():
    if request.method == 'POST':
        # Retrieve input from the request
        sex = request.form['sex']
        age = request.form['age']
        hypertension = request.form['hypertension']  
        heartdisease = request.form['heartdisease']
        married = request.form['evermarried']       
        worktype = request.form['worktype']
        avgglucose = request.form['avgglucose']
        bmi = request.form['bmi']
        smoking = request.form['smoking']
        predTarget = request.form['predictionTarget']
        refName = request.form['referenceName'] if predTarget == 'Others' else None


        form_array = np.array([[sex, age, hypertension, heartdisease, married, worktype, avgglucose, bmi, smoking]]).astype(float)
        sc_s = scStroke.transform(form_array)

        sc_s[0][6] = qtStroke[0].transform(sc_s[0][6].reshape(-1,1))
        sc_s[0][7] = qtStroke[1].transform(sc_s[0][7].reshape(-1,1))
        prediction = strokeModel.predict(sc_s)[0]
        prediction_percentage_true = strokeModel.predict_proba(sc_s)[0,1]
         # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Create a new Stroke object
        stroke = Stroke(
            s_userID=userID,
            s_sex=int(sex),
            s_age=int(age),
            s_hypertension=int(hypertension),
            s_heartdisease=int(heartdisease),
            s_married=int(married),
            s_worktype=int(worktype),
            s_avgglucose=float(avgglucose),
            s_BMI=float(bmi),
            s_smoking=int(smoking),
            s_stroke=int(prediction),
            s_feedback=None,  # Initialize feedback as None
            s_predtarget=predTarget,
            s_refname=refName
        )
        # Add the Stroke object to the database session
        db.session.add(stroke)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.strokeResult', user=user, sex=sex, age=age, hypertension=hypertension, heartdisease=heartdisease, married=married, worktype=worktype, 
                                avgglucose=avgglucose, bmi=bmi, smoking=smoking, prediction=prediction, prediction_percentage_true=prediction_percentage_true))
        
    return redirect(url_for('views.userdashboard'))

@views.route('/strokeResult' , methods=['GET','POST'])
def strokeResult():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
    sex=request.args.get('sex')
    age=request.args.get('age')
    hypertension=request.args.get('hypertension')
    heartdisease=request.args.get('heartdisease')
    married=request.args.get('married')
    worktype=request.args.get('worktype')
    avgglucose=request.args.get('avgglucose')
    bmi=request.args.get('bmi')
    smoking=request.args.get('smoking')

    prediction = request.args.get('prediction')
    prediction_percentage_true = float(request.args.get('prediction_percentage_true'))
    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('strokeResult.html', user=user, sex=int(sex), age=int(age), hypertension=int(hypertension), heartdisease=int(heartdisease), married=int(married), worktype=int(worktype),
                            avgglucose=int(avgglucose), bmi=int(bmi), smoking=int(smoking), prediction=int(prediction), prediction_percentage_true=prediction_percentage_true)

@views.route('/StrokeResultFeedback' , methods=['GET','POST'])
def strokeResultFeedback():
    if request.method == 'POST':
        # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')
        
        # Retrieve the feedback from the form
        feedback = request.form['s_feedback']

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Retrieve the latest Stroke record for the user
        stroke = Stroke.query.filter_by(s_userID=userID).order_by(Stroke.s_id.desc()).first()
        
        # Update the Stroke record with the user's feedback
        try:
            # Update the stroke record with the user's feedback
            stroke.s_feedback = feedback
            # Commit the changes to the database
            db.session.commit()
        except Exception as e:
            print(e)
            flash("Failed to submit stroke prediction feedback, please try again.")
        else:
            flash("Successfully submitted stroke prediction feedback.")

        return redirect(url_for('views.userdashboard', user=user))# Redirect to user dashboard after submitting feedback

    return render_template('userDashboard.html')

# Export Stroke CSV
@views.route('/exportStroke', methods=['GET'])
def exportStroke():
    # Get feedback data from the database
    stroke_data = Stroke.query.all()

    # Create a CSV string
    csv_stroke = create_stroke_csv(stroke_data)

    # Create a response with the CSV data
    response = Response(csv_stroke, mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='stroke.csv')

    return response

def create_stroke_csv(stroke_data):
    # Create a file-like object in memory
    csv_stroke = StringIO()
    csv_StrokeWriter = csv.writer(csv_stroke)

    # Write the header row
    csv_StrokeWriter.writerow(['s_id', 's_userID', 's_sex', 's_age', 's_hypertension', 's_heartdisease', 's_married', 's_worktype', 's_avgglucose', 
                         's_BMI', 's_smoking', 's_stroke', 's_feedback', 's_date'])
    
    # Write the stroke data rows
    for stroke in stroke_data:
        csv_StrokeWriter.writerow([stroke.s_id, stroke.s_userID, stroke.s_sex, stroke.s_age, stroke.s_hypertension, stroke.s_heartdisease, stroke.s_married, stroke.s_worktype, stroke.s_avgglucose, 
                             stroke.s_BMI, stroke.s_smoking, stroke.s_stroke, stroke.s_feedback, stroke.s_date])

    # Get the CSV data as a string
    csv_stroke.seek(0)
    csv_asthmaString = csv_stroke.getvalue()

    return csv_asthmaString
