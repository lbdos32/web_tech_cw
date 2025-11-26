from flask import Flask, render_template, url_for, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def root():
    return render_template('index.html')

BEHOLD_JSON_URL = 'https://feeds.behold.so/NMQlaZ9tJIAuwjIG7RIv'

@app.route('/latest-instagram')
def latest_instagram():
    try:
        res = requests.get(BEHOLD_JSON_URL)
        res.raise_for_status()
        data = res.json()
        # return only the latest post
        return jsonify(data['posts'][0])
    except Exception as e:
        print("Error fetching Behold JSON:", e)
        return jsonify({'error': 'Failed to fetch Instagram post'}), 500


@app.route("/healthAndSafety")
def health_and_safety():
    return render_template('healthAndSafety.html')

@app.route("/committee")
def committee():
    return render_template('committee.html')

