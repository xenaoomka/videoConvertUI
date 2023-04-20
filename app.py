import datetime
from flask import Flask, render_template, request, redirect, send_from_directory
from flask_bootstrap import Bootstrap
import sqlite3
import os
import pytz

app = Flask(__name__)
bootstrap = Bootstrap(app)

DB_NAME = '/app/content/videoConvert.db'
# '/Users/oomkaxena/Desktop/content/videoConvert.db'
# '/app/content/videoConvert.db'
VIDEO_DIRECTORY = '/app/content/output'
# '/Users/oomkaxena/Desktop/content/output'
# '/app/content/output'

# Convert UTC timestamp to MST
def convert_timestamp(timestamp):
    utc_timestamp = datetime.datetime.utcfromtimestamp(timestamp)
    utc_tz = pytz.timezone('UTC')
    mountain_tz = pytz.timezone('US/Mountain')
    mountain_timestamp = utc_tz.localize(utc_timestamp).astimezone(mountain_tz)
    return mountain_timestamp.strftime('%m/%d/%Y %I:%M %p')

@app.route('/')
def index():
    # Set the timezone to Mountain Time
    mountain_tz = pytz.timezone('US/Mountain')
    # Fetch all records from the database
    conn = sqlite3.connect(DB_NAME)
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

    return render_template('index.html', videos=videos, datetime=datetime)

@app.route('/update', methods=['POST'])
def update():
    # Update record in the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    file_id = request.form.get('id')
    claim_number = request.form.get('claim_number')
    ad_notes = request.form.get('ad_notes')
    c.execute('UPDATE converted_videos SET claim_number = ?, ad_notes = ? WHERE id = ?', (claim_number, ad_notes, file_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/play_video')
def play_video():
    return render_template('play_video.html')

@app.route('/video/<path:filename>')
def video(filename):
    """Route to serve video files."""
    # Check if the requested file exists in the video directory
    if filename in os.listdir(VIDEO_DIRECTORY):
        return send_from_directory(VIDEO_DIRECTORY, filename)
    else:
        return "Video not found", 404

@app.route('/play/<path:filename>')
def play(filename):
    """Route to play video files in a separate template page."""
    # Check if the requested file exists in the video directory
    if filename in os.listdir(VIDEO_DIRECTORY):
        return render_template('play.html', video_filename=filename)
    else:
        return "Video not found", 404

if __name__ == '__main__':
    app.run(debug=True)