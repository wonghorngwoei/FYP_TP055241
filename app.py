from website import create_app
from flask import Flask, render_template, url_for, request
import requests

app = create_app()

#MySQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tp055241@localhost/ldpms'

if __name__ == '__main__':
    app.run(debug=True)

# @app.route('/')
# def index():
#     return render_template('homepage.html')

# if __name__ == "__main__":
#     app.run(debug=True)

# $env:FLASK_DEBUG = "1" -- Run this before do your coding

# @app.route('/search', methods=['POST'])
# def search():
#     query = request.form['query']
#     api_key = 'AIzaSyDf-tSbLPvre8cFGB5IBGVK3PCwIAHxrJs'
#     url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query=hospitals+near+{query}&key={api_key}'

#     response = requests.get(url)
#     data = response.json()

#     # Extract the relevant information from the API response
#     results = data['results']
#     hospitals = []

#     for result in results:
#         name = result['name']
#         address = result['formatted_address']
#         hospitals.append({'name': name, 'address': address})

#     return render_template('results.html', hospitals=hospitals)
