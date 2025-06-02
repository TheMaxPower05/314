from flask import Flask, render_template, request, redirect, url_for, session, flash
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
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Incorrect email or password")
    return render_template('login.html')


@app.route('/home')
def dashboard():
    user_email = session.get('user')
    if not user_email:
        return redirect('/login')

    users = load_users()
    user = users.get(user_email)
    role = user.get("role", "")
    profile_pic = user.get("profile_pic", "") or "images/default_profile.jpg"

    with open('static/events.json') as f:
        events = json.load(f)

    # Only organiser sees their own events
    if role == "organiser":
        events = [e for e in events if e["organiser"] == user_email]

    friend_emails = user.get("friends", [])
    friends = [
        {
            "name": users[email]["first_name"],
            "image": users[email].get("profile_pic", "") or "images/defaultProfile.png"
        } for email in friend_emails if email in users
    ]

    return render_template("home.html", events=events, friends=friends, role=role, name=user["first_name"], profile_pic=profile_pic)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        fname = request.form['fname']
        lname = request.form['lname']
        password = request.form['password']
        role = request.form['role']  # from dropdown

        with open('users.json') as f:
            users = json.load(f)

        if email in users:
            return render_template('register.html', error="User already exists.")

        users[email] = {
            "first_name": fname,
            "last_name": lname,
            "password": password,
            "role": role,
            "friends": [],
            "profile_pic": ""
        }

        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)

        return redirect('/login')

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


@app.route('/fPassword', methods=['GET', 'POST'])
def fPass():
    if request.method == 'POST':
        email = request.form['email']
        users = load_users()
        if email in users:
            session['reset_email'] = email
            flash(f"Reset link sent to {email} (simulated).", 'info')
            return redirect(url_for('rPass'))
        else:
            flash("Email not found.", 'error')
    return render_template('fPassword.html')

@app.route('/reset', methods=['GET', 'POST'])
def rPass():
    email = session.get('reset_email')
    if not email:
        flash('Session expired or invalid.', 'error')
        return redirect(url_for('fPassword'))

    users = load_users()

    if email not in users:
        flash('User not found.', 'error')
        return redirect(url_for('fPassword'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            users[email]['password'] = new_password
            save_users(users)
            flash('Password successfully reset!', 'success')
            session.pop('reset_email', None)
            return redirect(url_for('fPass'))

    return render_template('reset.html')



@app.route('/search')
def search():
    query = request.args.get('q', '').lower()

    # Load users and events
    with open("users.json") as f:
        users = json.load(f)

    with open("static/events.json") as f:
        events = json.load(f)

    # Match events by title
    matched_events = [event for event in events if query in event['title'].lower()]

    matched_users = []
    for email,user_info in users.items():
        if (
            query in user_info.get("first_name", "").lower() or
            query in user_info.get("last_name", "").lower()
        ):
            matched_users.append({
                "name": f"{user_info['first_name']} {user_info['last_name']}",
                "image": user_info.get("profile_pic") or "images/defaultProfile.png"
            })
    return render_template(
        'eventSearch.html',
        events=matched_events,
        query=query,
        friends=matched_users,
        role=session.get('role', 'attendee')
    )

if __name__ == '__main__':
    app.run(debug=True)
