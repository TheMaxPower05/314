from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key'

USERS_FILE = 'users.json'

# Load user data
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save user data
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('auth'))
        else:
            return render_template('login.html', error="Incorrect email or password")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        fname = request.form['fname']
        lname = request.form['lname']
        password = request.form['password']

        repassword = request.form['repassword']
        email_pattern = r"^[\w\.-]+@(?:gmail\.com|hotmail\.com|yahoo\.com|outlook\.com)$"
        if not re.match(email_pattern, email):
            return render_template('register.html', error="Invalid email format")
        

        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[^\w\s]", password):
            return render_template('register.html', error="Password must be 8+ chars, include a number and symbol")
        
        
        if password != repassword:
            return render_template('register.html', error="Passwords do not match")

        users = load_users()
        if email in users:
            return render_template('register.html', error="User already exists")

        users[email] = {
            "first_name": fname,
            "last_name": lname,
            "password": password
        }
        save_users(users)
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Here you'd normally verify a code (e.g., OTP)
        return "Authentication Successful!"
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
