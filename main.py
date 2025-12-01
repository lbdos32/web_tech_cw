from flask import Flask, render_template, url_for, jsonify, request, redirect, session
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
import requests
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


app.config['CACHE_TYPE'] = 'SimpleCache'  # for production, use Redis or Memcached
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # (5 minutes)
cache = Cache(app)
BEHOLD_JSON_URL = 'https://feeds.behold.so/TkjBFP6CRMaCLOTV0n93'

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
def root():
    return render_template('index.html')

@app.route('/latest-instagram')
def latest_instagram():
    try:
        res = requests.get(BEHOLD_JSON_URL)
        res.raise_for_status()
        data = res.json()
        latest_post = data['posts'][0]
        return jsonify(latest_post)
    except Exception as e:
        print("Error fetching Behold JSON:", e)
        return jsonify({'error': 'Failed to fetch Instagram post'}), 500






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