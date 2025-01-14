from flask import Flask, render_template, request, jsonify
from api import api
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(api)
app.config['WTF_CSRF_ENABLED'] = False

headers = {
    'X-API-KEY': 'divyanshjindal',
    'Content-Type': 'application/json'
}

# Define a route for the homepage
@app.route('/')
def home():
    print('User IP', request.remote_addr)
    return render_template('index.html')  # Renders the HTML file

# Route to display the login form
@app.route('/login', methods=['GET'])
def login_form():
    print('User IP', request.remote_addr)
    return render_template('login.html')

# Route to display the chatbot
@app.route('/chatbot', methods=['GET'])
def chatbot():
    print('User IP', request.remote_addr)
    return render_template('ragbot.html')

# route for translation
@app.route('/translate', methods=['GET'])
def translate():
    print('User IP', request.remote_addr)
    return render_template('translate.html')



# Run the app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)  # debug=True for development; remove for production