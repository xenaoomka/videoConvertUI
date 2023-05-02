import datetime
from dotenv import load_dotenv
from flask import Flask, flash, render_template, request, redirect, send_from_directory, url_for
import sqlite3
import os
from flask_login import current_user, login_user
from flask_security import Security, SQLAlchemyUserDatastore, login_required, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_security.utils import hash_password
from flask_bcrypt import Bcrypt, check_password_hash
import pytz

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT')
app.config['SECURITY_REGISTERABLE'] = os.environ.get('SECURITY_REGISTERABLE')


db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    fs_uniquifier = db.Column(db.String(64), unique=True)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Create the database tables
db.create_all()

# Create a UserDatastore object
user_datastore = SQLAlchemyUserDatastore(db, User, Role)

# Initialize the Flask-Security extension
security = Security(app, user_datastore)

# Create a new user and hash their password
with app.app_context():
    if not User.query.filter_by(email=os.environ.get('USER_EMAIL')).first():
        email = os.environ.get('USER_EMAIL')
        password = os.environ.get('USER_PASSWORD')
        user_datastore.create_user(email=email, password=hash_password(password))
        db.session.commit()

# Convert UTC timestamp to MST
def convert_timestamp(timestamp):
    utc_timestamp = datetime.datetime.utcfromtimestamp(timestamp)
    utc_tz = pytz.timezone('UTC')
    mountain_tz = pytz.timezone('US/Mountain')
    mountain_timestamp = utc_tz.localize(utc_timestamp).astimezone(mountain_tz)
    return mountain_timestamp.strftime('%m/%d/%Y %I:%M %p')

@app.route('/')
@login_required
def home():
    # Set the timezone to Mountain Time
    mountain_tz = pytz.timezone('US/Mountain')
    # Fetch all records from the database
    conn = sqlite3.connect(os.getenv('DB_NAME'))
    c = conn.cursor()
    c.execute('SELECT id, original_file_name, original_file_date, converted_file_name, converted_file_date, claim_number, ad_notes FROM converted_videos')
    videos = c.fetchall()
    
    # Convert timestamps to MST
    for i in range(len(videos)):
        original_file_date = videos[i][2]
        converted_file_date = videos[i][4]
        videos[i] = (
            videos[i][0],
            videos[i][1],
            convert_timestamp(original_file_date),
            videos[i][3],
            convert_timestamp(converted_file_date),
            videos[i][5],
            videos[i][6]
    )

    conn.close()

    return render_template('home.html', videos=videos, datetime=datetime)

@app.route('/update', methods=['POST'])
@login_required
def update():
    # Update record in the database
    conn = sqlite3.connect(os.environ.get('DB_NAME'))
    c = conn.cursor()
    file_id = request.form.get('id')
    claim_number = request.form.get('claim_number')
    ad_notes = request.form.get('ad_notes')
    c.execute('UPDATE converted_videos SET claim_number = ?, ad_notes = ? WHERE id = ?', (claim_number, ad_notes, file_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/play_video')
@login_required
def play_video():
    return render_template('play_video.html')

@app.route('/video/<path:filename>')
@login_required
def video(filename):
    """Route to serve video files."""
    # Check if the requested file exists in the video directory
    if filename in os.listdir(os.environ.get('VIDEO_DIRECTORY')):
        return send_from_directory(os.environ.get('VIDEO_DIRECTORY'), filename)
    else:
        return "Video not found", 404

@app.route('/play/<path:filename>')
@login_required
def play(filename):
    """Route to play video files in a separate template page."""
    # Check if the requested file exists in the video directory
    if filename in os.listdir(os.environ.get('VIDEO_DIRECTORY')):
        return render_template('play.html', video_filename=filename)
    else:
        return "Video not found", 404

if __name__ == '__main__':
    app.run(debug=True)