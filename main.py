
from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/healthAndSafety")
def health_and_safety():
    return render_template('healthAndSafety.html')

@app.route("/committee")
def committee():
    return render_template('committee.html')

