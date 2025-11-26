from flask import Flask, render_template, url_for, jsonify
from flask_caching import Cache
import requests

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

@app.route("/committee")
def committee():
    return render_template('committee.html')

