from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/static-example/img")
def static_example_img():
    start = '<img src ="'
    url = url_for('static', filename ='screenshot_test.png')
    end = '">'
    return start + url + end , 200