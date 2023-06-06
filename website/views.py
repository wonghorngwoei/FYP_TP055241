from flask import Flask, Blueprint, render_template, url_for, request
import requests

views = Blueprint('views', __name__)


@views.route('/')
def homepage():
    return render_template('homepage.html')

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
        hospitals.append({'name': name, 'address': address})

    return render_template('results.html', hospitals=hospitals)