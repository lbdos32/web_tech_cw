from flask import Flask, render_template, url_for, jsonify, request, redirect, session
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)


# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///committee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/committee'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database model
class CommitteeMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    info = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(200), nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

app.secret_key = 'mysecretkey'  # needed for sessions

# --- Admin credentials (hardcoded for now) ---
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('committee'))
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('root'))

@app.route("/")
def index():
    post = fetch_latest_instagram_post()
    return render_template("index.html", post=post)

@app.route("/healthAndSafety")
def health_and_safety():
    return render_template('healthAndSafety.html')


UPLOAD_FOLDER = 'static/committee'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Temporary storage of committee members
committee_members = []

@app.route("/committee")
def committee():
    members = CommitteeMember.query.all()
    return render_template("committee.html", committee=members)

@app.route("/committee/add", methods=['POST'])
def add_committee_member():
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    role = request.form['role']
    name = request.form['name']
    info = request.form['info']
    photo_file = request.files.get('photo')
    filename = None

    if photo_file and photo_file.filename != '':
        filename = secure_filename(photo_file.filename)
        photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    member = CommitteeMember(role=role, name=name, info=info, photo=filename)
    db.session.add(member)
    db.session.commit()

    return redirect(url_for('committee'))

@app.route("/committee/delete/<int:member_id>", methods=['POST'])
def delete_committee_member(member_id):
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    member = CommitteeMember.query.get_or_404(member_id)

    # Delete the photo from disk if exists
    if member.photo:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], member.photo)
        if os.path.exists(photo_path):
            os.remove(photo_path)

    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('committee'))

# Instagram posting

INSTAGRAM_ACCESS_TOKEN = "IGAAP89WJOTqFBZAFIxMWRDRlVfRUkycVA5VWYyV1lZAV2YxNVZA4VG5QbF9VWEpwNjZAkUFlNckVKeHlXNi1jdFZA2ZAUQ3enp3NGx4djlHb3NpT0JQa044UlZABQl9GTXY5TzNEZA3VzSlhWRllCeHFnZAGNmY2NwR2pKTGJza0tRSk96YwZDZD"
REFRESH_INTERVAL = 300  # seconds (5 minutes) — change as needed

cached_post = None
last_fetch_time = 0


def fetch_latest_instagram_post():
    global cached_post, last_fetch_time

    now = time.time()
    if cached_post and (now - last_fetch_time < REFRESH_INTERVAL):
        return cached_post  # return cached data

    url = (
        "https://graph.instagram.com/me/media"
        "?fields=id,media_url,caption,timestamp"
        f"&access_token={INSTAGRAM_ACCESS_TOKEN}"
    )

    response = requests.get(url)
    data = response.json()

    if "data" not in data or len(data["data"]) == 0:
        return None

    latest = data["data"][0]  # newest post

    cached_post = {
        "image_url": latest.get("media_url"),
        "caption": latest.get("caption", ""),
        "timestamp": latest.get("timestamp")
    }
    last_fetch_time = now

    return cached_post



