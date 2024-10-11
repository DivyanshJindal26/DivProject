from flask import Flask, render_template, request, jsonify
from api import api
import requests

app = Flask(__name__)
app.register_blueprint(api)
app.config['WTF_CSRF_ENABLED'] = False

defaultAPI = 'http://127.0.0.1:5000/api/'
headers = {
    'X-API-KEY': 'divyanshjindal',
    'Content-Type': 'application/json'
}

# Define a route for the homepage
@app.route('/')
def home():
    return render_template('index.html')  # Renders the HTML file

# Route to display the login form
@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')



# Run the app
if __name__ == '__main__':
    app.run(debug=True)  # debug=True for development; remove for production