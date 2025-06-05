from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import json
import os
import re
from werkzeug.utils import secure_filename
from urllib.parse import quote, unquote





app = Flask(__name__)
app.secret_key = 'your-secret-key'

USERS_FILE = 'users.json'

with open('static/events.json') as f:
    events = json.load(f)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

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
    profile_pic = user.get("profile_pic", "") or "images/defaultProfile.png"

    with open('static/events.json') as f:
        events = json.load(f)

    if role == "organiser":
        events = [e for e in events if e["organiser"] == user_email]

    friend_emails = user.get("friends", [])
    friends = [
        {
            "email": email,
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
        role = request.form['role']  

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

    with open("users.json") as f:
        users = json.load(f)

    user_email = session.get('user')
    user = users.get(user_email)
    profile_pic = user.get("profile_pic", "") or "images/defaultProfile.png"


    with open("static/events.json") as f:
        events = json.load(f)

    matched_events = [event for event in events if query in event['title'].lower() or query in event['location'].lower()]

    matched_users = []
    for email,user_info in users.items():
        if (

            query in user_info.get("first_name", "").lower() or
            query in user_info.get("last_name", "").lower()
        ):
            matched_users.append({
                "email": email,
                "name": f"{user_info['first_name']} {user_info['last_name']}",
                "image": user_info.get("profile_pic") or "images/defaultProfile.png"
            })

    return render_template(
        'eventSearch.html',
        events=matched_events,
        query=query,
        friends=matched_users,
        role=session.get('role', 'attendee'),
        profile_pic=profile_pic

    )



@app.route('/tickets/<int:eventId>')
def tickets(eventId):

    with open("users.json") as f:
        users = json.load(f)
    user_email = session.get('user')
    user = users.get(user_email)
    profile_pic = user.get("profile_pic", "") or "images/defaultProfile.png"
  
    with open("static/events.json") as f:
        events = json.load(f)


    event = next((e for e in events if e['id'] == eventId), None)
    if event:
        return render_template('getTickets.html', event=event, profile_pic=profile_pic)
    else:
        abort(404)


def getEventById(eventId):
    with open('static/events.json') as f:
        events = json.load(f)
    for event in events:
        if str(event['id']) == str(eventId):
            return event  

@app.route('/confirm', methods=['POST'])
def confirm():
    eventId = request.form.get('event_id')
    name = request.form.get('name')
    email = session.get('user')
    quantity = request.form.get('quantity')

    if not eventId or not name or not email or not quantity:
        return "Missing form data", 400

    try:
        quantity = int(quantity)
    except ValueError:
        return "Invalid quantity", 400


    event = getEventById(eventId)
    if event is None:
        return "Event not found", 404


    with open('users.json', 'r') as file:
        users = json.load(file)


    user_email = session.get('user')
    user = users.get(user_email)
    profile_pic = user.get("profile_pic", "") or "images/defaultProfile.png"


    if email not in users:
        return "User not found", 404

    if 'attendingEvents' not in users[email]:
        users[email]['attendingEvents'] = []

    
    attending = users[email]['attendingEvents']
    found = False

    for e in attending:
        if str(e['eventId']) == str(eventId):
            e['ticketCount'] += quantity
            found = True
            break

    if not found:
        attending.append({
            "eventId": eventId,
            "eventName": event['title'],
            "ticketCount": quantity
        })

    with open('users.json', 'w') as file:
        json.dump(users, file, indent=2)
    return render_template("confirmation.html", name=name, event=event, quantity=quantity, profile_pic=profile_pic)


@app.route('/createEvent', methods=['GET', 'POST'])
def createEvent():
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        time = request.form['time']
        city = request.form['city']
        state = request.form['state']
        price = request.form['price']
        description = request.form['description']
        organiser = session.get('user')  

        if not all([title, date, time, city, state, price, description]):
            return render_template("createEvent.html", error="Please Fill All Fields")

        datetime_str = f"{date}T{time}"
        location = f"{city}, {state}"

        filename = ''
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                filename = secure_filename(image.filename)
                filepath = os.path.join('static/images', filename)  
                image.save(filepath)
                image_path = f'images/{filename}'  
            else:
                image_path = ""

        with open('static/events.json', 'r') as f:
            events = json.load(f)

        new_event = {
            "id": max(event["id"] for event in events) + 1,
            "title": title,
            "description": description,
            "datetime": datetime_str,
            "image": image_path,
            "organiser": organiser,
            "location": location,
            "price": float(price)

        }

        events.append(new_event)

        with open('static/events.json', 'w') as f:
            json.dump(events, f, indent=2)

        return redirect(url_for('dashboard'))

    return render_template("createEvent.html")


@app.route('/payment', methods=['POST'])
def payment():
    eventId = request.form.get('event_id')
    quantity = request.form.get('quantity')
    name = request.form.get('name')
    email = session.get('user')

    if not eventId or not quantity or not name or not email:
        return "Missing data", 400

    try:
        quantity = int(quantity)
    except ValueError:
        return "Invalid quantity", 400

    event = getEventById(eventId)
    if not event:
        return "Event not found", 404

    total_price = quantity * float(event.get("price", 0))
    
    with open('users.json') as f:
        users = json.load(f)
    user_email = session.get('user')
    profile_pic = users[user_email].get("profile_pic", "") or "images/defaultProfile.png"
    return render_template("payment.html", event=event, quantity=quantity, total_price=total_price, name=name, email=email, profile_pic=profile_pic)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    userEmail = session['user']

    with open('users.json') as f:
        users = json.load(f)

    user = users.get(userEmail)
    if not user:
        return redirect(url_for('login'))

    with open('static/events.json') as f:
        events = json.load(f)

    event_lookup = {str(e['id']): e for e in events}

    attendingInfo = []
    for evt in user.get('attendingEvents', []):
        eventId = str(evt.get('eventId'))
        event = event_lookup.get(eventId)
        if event:
            attendingInfo.append({
                'title': event['title'],
                'ticketCount': evt.get('ticketCount', 0)
            })

    organisedInfo = []
    if user.get('role') == 'organiser':
        organisedInfo = [e for e in events if e.get('organiser') == userEmail]


    friendProfiles = []
    for friendEmail in user.get('friends', []):
        friend = users.get(friendEmail)
        if not friend:
            continue

        friendAttending = []
        for evt in friend.get('attendingEvents', []):
            eventId = str(evt.get('eventId'))
            event = event_lookup.get(eventId)
            if event:
                friendAttending.append({
                    'eventName': event['title'],
                    'ticketCount': evt.get('ticketCount', 1)
                })

        friendProfiles.append({
            'name': friend['first_name'],
            'email': friendEmail,
            'profilePic': friend.get('profile_pic', '') or "images/defaultProfile.png",
            'attending': friendAttending
        })

    with open('static/events.json') as f:
        events = json.load(f)



    return render_template('profile.html',
                           user=user,
                           attendingEvents=attendingInfo,
                           organisedEvents=organisedInfo,
                           friendProfiles=friendProfiles,
                           profile_pic=user.get('profile_pic', '') or "images/defaultProfile.png")

@app.route('/cancelAttendance/<int:index>', methods=['POST'])
def cancelAttendance(index):
    if 'user' not in session:
        return "Unauthorized", 401

    users = load_users()
    user_email = session['user']
    user = users.get(user_email)

    if user and 'attendingEvents' in user and 0 <= index < len(user['attendingEvents']):
        del user['attendingEvents'][index]
        save_users(users)
        return '', 204
    return "Event not found", 404


@app.route('/deleteEvent/<int:eventId>', methods=['POST'])
def deleteEvent(eventId):
    if 'user' not in session:
        return "Unauthorized", 401

    with open('static/events.json') as f:
        events = json.load(f)

    updated_events = [e for e in events if e['id'] != eventId]

    with open('static/events.json', 'w') as f:
        json.dump(updated_events, f, indent=2)

    return '', 204


@app.route('/editProfile', methods=['POST'])
def editProfile():
    if 'user' not in session:
        return redirect(url_for('login'))

    old_email = session['user']

    with open('users.json') as f:
        users = json.load(f)

    user = users.get(old_email)
    if not user:
        return redirect(url_for('login'))

    new_email = request.form.get('email', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    file = request.files.get('profilePic')

    if first_name:
        user['first_name'] = first_name
    if last_name:
        user['last_name'] = last_name

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file_path = os.path.join('static/images', filename)
        file.save(file_path)
        user['profile_pic'] = f'images/{filename}'

    if new_email and new_email != old_email:
        users[new_email] = user
        del users[old_email]
        session['user'] = new_email
    else:
        users[old_email] = user

    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

    return redirect(url_for('profile'))

@app.route('/friend/<path:email>', methods=['GET', 'POST'])
def friendProfile(email):
    print("Requested email:", email)
    
    email = unquote(email)  
    users = load_users()
    currentUser = session.get('user')

    if not currentUser or email not in users:
        abort(404)

    profile = users[email]
    current_user = users[currentUser]
    is_friend = email in current_user.get('friends', [])

    profile_pic = current_user.get("profile_pic", "images/default_profile.jpg")

    return render_template(
        'friendPfp.html',
        profile=profile,
        profile_email=email,
        is_friend=is_friend,
        profile_pic=profile_pic
    )

@app.route('/addFriend/<path:email>', methods=['POST'])
def addFriend(email):
    email = unquote(email)
    users = load_users()
    currentUser = session.get('user')

    if not currentUser or email not in users:
        abort(404)

    if email not in users[currentUser].get('friends', []):
        users[currentUser].setdefault('friends', []).append(email)

        users[email].setdefault('friends', []).append(currentUser)

        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

    return redirect(url_for('friendProfile', email=email))

@app.route('/removeFriend/<path:email>', methods=['POST'])
def removeFriend(email):
    email = unquote(email)
    users = load_users()
    currentUser = session.get('user')

    if not currentUser or email not in users:
        abort(404)

    if email in users[currentUser].get('friends', []):
        users[currentUser]['friends'].remove(email)

    if currentUser in users[email].get('friends', []):
        users[email]['friends'].remove(currentUser)

    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

    return redirect(url_for('friendProfile', email=email))


from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import json
import os

@app.route('/editEvent', methods=['POST'])
def editEvent():
    event_id = int(request.form['id'])
    title = request.form['title']
    description = request.form['description']
    datetime = request.form['datetime']
    location = request.form['location']
    price = request.form['price']
    image = request.files.get('image')

    events_path = os.path.join('static', 'events.json')

    with open(events_path, 'r') as f:
        events = json.load(f)

    for event in events:
        if event['id'] == event_id:
            event['title'] = title
            event['description'] = description
            event['datetime'] = datetime
            event['location'] = location
            event['price'] = price

            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join('static', 'images', filename))
                event['image'] = f'images/{filename}'
            break

    with open(events_path, 'w') as f:
        json.dump(events, f, indent=2)

    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(debug=True)
