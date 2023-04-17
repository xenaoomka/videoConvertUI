from flask import Flask, render_template, request, redirect, send_from_directory
from flask_bootstrap import Bootstrap
import sqlite3
import os

app = Flask(__name__)
bootstrap = Bootstrap(app)

DB_NAME = '/app/content/videoConvert.db'
VIDEO_DIRECTORY = '/app/content/output'

@app.route('/')
def index():
    # Fetch all records from the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, original_file_name, converted_file_name, claim_number, ad_notes FROM converted_videos')
    videos = c.fetchall()
    conn.close()
    return render_template('index.html', videos=videos)

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
