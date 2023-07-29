from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
import requests
import sqlite3
import os
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# Accéder aux variables d'environnement
secret_key = os.getenv("SECRET_KEY")
mail_server = os.getenv("MAIL_SERVER")
mail_username = os.getenv("MAIL_USERNAME")
mail_password = os.getenv("MAIL_PASSWORD")
mail_recipient = os.getenv("MAIL_RECIPIENT")
sms_api_url = os.getenv("SMS_API_URL")
sms_api_user = os.getenv("SMS_API_USER")
sms_api_password = os.getenv("SMS_API_PASSWORD")


# Utiliser les variables d'environnement dans votre code
print(f"Server: {mail_server}")
print(f"Mail username: {mail_username }")
print(f"Password: {mail_password}")
print(f"Recipient: {mail_recipient}")
print(f"SMS API User: {sms_api_user }")
print(f"SMS API Password: {sms_api_password }")

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key  # Replace with a secure secret key

# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = 25  # Use the appropriate port for your mail server
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = mail_server
app.config['MAIL_PASSWORD'] = mail_password
app.config['MAIL_DEFAULT_SENDER'] = 'g'

mail = Mail(app)

# Configuration for SQLite database
DB_NAME = "activities.db"

# Create the database and tables using schema.sql if it doesn't exist
if not os.path.exists(DB_NAME):
    with sqlite3.connect(DB_NAME) as conn:
        with open('schema.sql') as f:
            conn.executescript(f.read())

@app.route('/')
def index():
    location_id = request.args.get('location', None)  # Get the location ID from query parameters
    if location_id != None:
        location_id = int(location_id)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Fetch the locations for the location selector
        cursor.execute("SELECT * FROM locations")
        locations = cursor.fetchall()

        # Fetch activities filtered by the selected location (if provided)
        if location_id is not None:
            cursor.execute("SELECT * FROM activities WHERE is_deleted = 0 AND location_id = ?", (location_id,))
        else:
            cursor.execute("SELECT * FROM activities WHERE is_deleted = 0")

        activities = cursor.fetchall()

    return render_template('index.html', activities=activities, locations=locations, location_id=location_id)

@app.route('/activity/add', methods=['GET', 'POST'])
def add_activity():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        location_id = request.form['location']

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO activities (name, description, date, time, location_id) VALUES (?, ?, ?, ?, ?)",
                           (name, description, date, time, location_id))
            conn.commit()

        return redirect(url_for('index'))

    # Fetch locations to display in the form
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations")
        locations = cursor.fetchall()

    return render_template('add_activity.html', locations=locations)

@app.route('/activity/edit/<int:activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        location_id = request.form['location']

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE activities SET name=?, description=?, date=?, time=?, location_id=? WHERE id=?",
                           (name, description, date, time, location_id, activity_id))
            conn.commit()

        return redirect(url_for('index'))

    # Fetch the activity to display in the form for editing
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE id=?", (activity_id,))
        activity = cursor.fetchone()

        cursor.execute("SELECT * FROM locations")
        locations = cursor.fetchall()

    return render_template('edit_activity.html', activity=activity, locations=locations)

@app.route('/activity/delete/<int:id>')
def delete_activity(id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE activities SET is_deleted = 1 WHERE id = ?", (id,))
        conn.commit()

    return redirect(url_for('index'))

@app.route('/send_email')
def send_email():
    location_id = request.args.get('location', None)  # Get the location ID from query parameters

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Fetch the locations for the location selector
        cursor.execute("SELECT * FROM locations")
        locations = cursor.fetchall()

        # Fetch activities filtered by the selected location (if provided)
        if location_id is not None:
            cursor.execute("SELECT * FROM activities WHERE is_deleted = 0 AND location_id = ?", (location_id,))
        else:
            cursor.execute("SELECT * FROM activities WHERE is_deleted = 0")

        activities = cursor.fetchall()

    recipient = mail_recipient
    subject = activities[0][1]
    body = activities[0][2]

    message = Message(subject=subject, recipients=[recipient], body=body)

    try:
        mail.send(message)
        flash('Email sent successfully!', 'success')
    except Exception as e:
        flash(f'Failed to send email. Error: {str(e)}', 'danger')

    return redirect(url_for('index'))

@app.route('/send_sms')
def send_sms(user, password, msg):
    try:
        base_url = 'https://smsapi.free-mobile.fr/sendmsg/'
        params = {
            'user': user,
            'password': password,
            'msg': msg
        }

        response = requests.get(base_url, params=params)
        print(response)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()  # Assuming the response contains JSON data
            return data
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
user = sms_api_user
password = sms_api_password
msg = "Hello from Python !"

# Replace 'YOUR_API_URL' with the actual base URL you want to make the GET request to
response_data = send_sms(user, password, msg)

if response_data:
    # Process and use the response data here
    print(response_data)

if __name__ == '__main__':
    app.run(debug=True)
