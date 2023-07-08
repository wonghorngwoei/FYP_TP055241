from flask import Blueprint, render_template, redirect, url_for, request, session, flash, Response
from .models import User, Feedback, Admin, Asthma, Diabetes, Stroke
from . import db
from io import StringIO
import requests
import pickle
import csv
import numpy as np



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

    return render_template('userdashboard.html', user = user)

def index():
    active_tab = request.args.get('active_tab', 'home')
    return render_template('userDashboard.html', active_tab=active_tab)


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
            print("Updated user!")
            return redirect(url_for('views.userdashboard'))
        except:
            return "Error 404: Could not update user"
    
    else:
        return render_template('userDashboard.html', user=user)

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
            flash('Note is too short!',category='error')
        else:
            new_feedback = Feedback(f_feedback=feedback, f_userID=userID)
            db.session.add(new_feedback)
            db.session.commit()
            flash('Note added!', category='success')
            return redirect(url_for('views.userdashboard'))
        
    return render_template('userDashboard.html')


##### Admin Dashboard Functions #####
@views.route('/admindashboard', methods=['GET','POST'])
def admindashboard():
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')

    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)
    return render_template('adminDashboard.html', admin = admin)


# Route for the edit profile page
@views.route('/edit-aprofile/<int:a_id>', methods=['GET', 'POST'])
def editAdminProfile(a_id):
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
    
# Manage User Account (Admin)
@views.route('/manageUserAccount', methods=['GET','POST'])
def getUserInfo():
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')

    # Fetch the user's data from the database
    user = User.query.all()
    print(user)

    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)
    return render_template('manageUserAccount.html', admin = admin, user=user)

@views.route('/delete_user/<int:u_id>', methods=['GET', 'POST'])
def deleteUser(u_id):
    # Retrieve the user ID from the session or wherever it's stored
    adminID = session.get('a_id')
    # Retrieve the user from the database based on the user_id
    userdel = User.query.get_or_404(u_id)
    # Retrieve all users from the database
    user = User.query.all()
    # Fetch the user's data from the database
    admin = Admin.query.get(adminID)

    try:
        # Delete the user from the database
        db.session.delete(userdel)
        db.session.commit()
        flash("User Deleted Successully.")

        # Redirect to the user account page or any other desired page
        return redirect(url_for('views.getUserInfo'))

    except:
        flash("Problem deleting the user account.")
            # Redirect to the user account page or any other desired page
        return redirect(url_for('views.getUserInfo'))


# Route for the edit profile page
@views.route('/edit_user/<int:u_id>', methods=['GET', 'POST'])
def editUser(u_id):
    # Retrieve the user from the database based on the user_id
    user = User.query.get_or_404(u_id)

    if request.method == 'POST':
        # Update the user's information based on the form data
        user.u_fname = request.form['u_fname']
        user.u_lname = request.form['u_lname']
        user.u_email = request.form['u_email']
        user.u_age = request.form['u_age']
        user.u_gender = request.form['u_gender']
        user.u_hpnumber = request.form['u_hpnumber']
        user.u_address = request.form['u_address']

        # Save the changes to the database
        db.session.commit()

        # Redirect to the user account page or any other desired page
        return redirect(url_for('views.getUserInfo'))

    # Render the edit user form with the pre-filled user information
    return render_template('manageUserAccount.html', user=user)

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
        )
        # Add the Asthma object to the database session
        db.session.add(asthma)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.asthmaResult', user=user, prediction=prediction, prediction_percentage_true=prediction_percentage_true))
        
    return redirect(url_for('views.userdashboard'))

@views.route('/asthmaResult' , methods=['GET','POST'])
def asthmaResult():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
    prediction = request.args.get('prediction')
    

    prediction_percentage_true = float(request.args.get('prediction_percentage_true'))

    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('asthmaResult.html', user=user, prediction=int(prediction), prediction_percentage_true=prediction_percentage_true)

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
        asthma.am_feedback = feedback

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.userdashboard', user=user))  # Redirect to user dashboard after submitting feedback

    return render_template('userDashboard.html')

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
        )
        # Add the Diabetes object to the database session
        db.session.add(diabetes)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.diabetesResult', user=user, prediction=prediction, diabetes=diabetes, prediction_percentage_true=prediction_percentage_true))
        
    return redirect(url_for('views.userdashboard'))

@views.route('/diabetesResult' , methods=['GET','POST'])
def diabetesResult():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
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
        diabetes.d_feedback = feedback

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.userdashboard', user=user))  # Redirect to user dashboard after submitting feedback

    return render_template('userDashboard.html')

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
            s_feedback=None  # Initialize feedback as None
        )
        # Add the Stroke object to the database session
        db.session.add(stroke)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.strokeResult', user=user, prediction=prediction, prediction_percentage_true=prediction_percentage_true))
        
    return redirect(url_for('views.userdashboard'))

@views.route('/strokeResult' , methods=['GET','POST'])
def strokeResult():
    # Retrieve the user ID from the session or wherever it's stored
    userID = session.get('u_id')
    # Retrieve the result from the query parameter
    prediction = request.args.get('prediction')
    prediction_percentage_true = float(request.args.get('prediction_percentage_true'))
    # Fetch the user's data from the database
    user = User.query.get(userID)

    return render_template('strokeResult.html', user=user, prediction=int(prediction), prediction_percentage_true=prediction_percentage_true)

@views.route('/StrokeResultFeedback' , methods=['GET','POST'])
def strokeResultFeedback():
    if request.method == 'POST':
        # Retrieve the user ID from the session or wherever it's stored
        userID = session.get('u_id')
        
        # Retrieve the feedback from the form
        feedback = request.form['d_feedback']

        # Fetch the user's data from the database
        user = User.query.get(userID)

        # Retrieve the latest Stroke record for the user
        stroke = Stroke.query.filter_by(d_userID=userID).order_by(Stroke.d_id.desc()).first()
        
        # Update the stroke record with the user's feedback
        stroke.s_feedback = feedback

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('views.userdashboard', user=user))  # Redirect to user dashboard after submitting feedback

    return render_template('userDashboard.html')
