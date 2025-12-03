from flask import Flask, render_template, url_for, jsonify, request, redirect, session
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///committee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Database model
class CommitteeMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    embed = db.Column(db.String(1024), nullable=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

app.secret_key = 'mysecretkey'

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
    return redirect(url_for("index"))

@app.route("/")
def index():
    post = fetch_latest_instagram_post()
    return render_template("index.html", post=post)

@app.route("/healthAndSafety")
def health_and_safety():
    return render_template('healthAndSafety.html')


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


@app.route("/announcements")
def announcements():
    announce = Announcement.query.all()

    return render_template("announcements.html", announcements=announce)

@app.route("/announcements/add", methods=['POST'])
def add_committee_member():
    if not session.get('admin_logged_in'):
        return "Unauthorized", 403

    id = request.form['id']
    title = request.form['title']
    description = request.form['description']
    image = request.form['image']
    filename = None

    announce = Announcement(embed=embed)
    db.session.add(announce)
    db.session.commit()

    return redirect(url_for('announcements'))







# Instagram posting

INSTAGRAM_ACCESS_TOKEN = "IGAAP89WJOTqFBZAFRxaGFKa2d2aWZAMQUxkYVNVRE11ajdhV3N6UEtza1dmM21xd01iUndCRUg2ZAWxkUHVBQXVndF9BczUtWldjSnJaVGZAJaEkyVW15cTZALaldaSjI1RGtMX1BIMmdrZAGhNU1RWUmNFMkZAid0Q3M0NHU2cyZAWotdwZDZD"
REFRESH_INTERVAL = 500  # seconds

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



