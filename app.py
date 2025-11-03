from retinopathy import app
from flask import Flask
from flask import render_template


# This is the object Gunicorn looks for
app = Flask(__name__)


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')