from flask import Flask, render_template, url_for, jsonify, request, redirect
from flask_caching import Cache
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['CACHE_TYPE'] = 'SimpleCache'  # for production, use Redis or Memcached
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # (5 minutes)

cache = Cache(app)
BEHOLD_JSON_URL = 'https://feeds.behold.so/NMQlaZ9tJIAuwjIG7RIv'

@app.route("/")
def root():
    return render_template('index.html')

@app.route('/latest-instagram')
@cache.cached()  # this caches the route automatically
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

@app.route("/committee", methods=['GET'])
def committee():
    return render_template("committee.html", committee=committee_members)

@app.route("/committee/add", methods=['POST'])
def add_committee_member():
    role = request.form['role']
    name = request.form['name']
    info = request.form['info']
    photo_file = request.files.get('photo')
    filename = None

    if photo_file and photo_file.filename != '':
        filename = secure_filename(photo_file.filename)
        photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    member = {
        'role': role,
        'name': name,
        'info': info,
        'photo': filename
    }
    committee_members.append(member)

    return redirect(url_for('committee'))
