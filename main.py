from flask import Flask, render_template, url_for, jsonify, request, redirect, session, flash
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from functools import wraps
import requests
import time
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
#gets secret key from .env file

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#db


UPLOAD_FOLDER = 'static/announcements'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database models
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=True)

class CommitteeMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    embed = db.Column(db.String(1024), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

with app.app_context():
    db.create_all()

# --------- admin --------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']  # username = email
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user:
            error = "Invalid username or password"
            return render_template('login.html', error=error)

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            error = "Invalid username or password"
            return render_template('login.html', error=error)

        session['admin_logged_in'] = True
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for("index"))

@app.route('/ResetPassword', methods=['GET', 'POST'])
def reset_password():
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    if request.method == "POST":
        email = request.form["email"]
        current_password = request.form["CurrentPassword"]
        new_password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if not user:
            return "User not found", 404

        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash):
            return "Incorrect current password", 400

        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.password_hash = new_password_hash
        db.session.commit()

        return "Password updated successfully!", render_template("login.html")

    return render_template("resetPassword.html")


#Homepage/root
@app.route("/")
def index():
    post = fetch_latest_instagram_post()
    return render_template("index.html", post=post)


@app.route("/healthAndSafety")
def health_and_safety():
    return render_template('healthAndSafety.html')

# --------- Committee --------- #

@app.route("/committee")
def committee():
    members = CommitteeMember.query.all()
    return render_template("committee.html", committee=members)

@app.route("/committee/add", methods=['POST'])
def add_committee_member():
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    embed = request.form['embed']
    filename = None

    member = CommitteeMember(embed=embed)
    db.session.add(member)
    db.session.commit()

    return redirect(url_for('committee'))


@app.route("/committee/delete/<int:member_id>", methods=['POST'])
def delete_committee_member(member_id):
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    member = CommitteeMember.query.get_or_404(member_id)

    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('committee'))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------- Announcements --------- #
@app.route("/announcements")
def announcements():
    announce = Announcement.query.all()

    return render_template("announcements.html", announcements=announce)

@app.route("/announcements/add", methods=['POST'])
def add_announcements():
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    title = request.form['title']
    description = request.form['description']
    photo_file = request.files.get('photo')
    filename = None

    if photo_file and photo_file.filename != '':
        filename = secure_filename(photo_file.filename)
        photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    announce = Announcement(title=title, description=description, photo=filename)
    db.session.add(announce)
    db.session.commit()

    return redirect(url_for('announcements'))

@app.route("/announcement/delete/<int:announcement_id>", methods=['POST'])
def delete_announcement(announcement_id):
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    announce = Announcement.query.get_or_404(announcement_id)

    db.session.delete(announce)
    db.session.commit()
    return redirect(url_for('announcements'))


# --------- Instagram posting --------- #

INSTAGRAM_ACCESS_TOKEN = "IGAAP89WJOTqFBZAFRxaGFKa2d2aWZAMQUxkYVNVRE11ajdhV3N6UEtza1dmM21xd01iUndCRUg2ZAWxkUHVBQXVndF9BczUtWldjSnJaVGZAJaEkyVW15cTZALaldaSjI1RGtMX1BIMmdrZAGhNU1RWUmNFMkZAid0Q3M0NHU2cyZAWotdwZDZD"
REFRESH_INTERVAL = 300  # seconds, 5 mins

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


