from flask import Flask, render_template, request, redirect, send_from_directory
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination, get_page_parameter
import sqlite3
import os

app = Flask(__name__)
bootstrap = Bootstrap(app)

DB_NAME = '/Users/oomkaxena/Desktop/content/videoConvert.db'
# '/Users/oomkaxena/Desktop/content/videoConvert.db'
# '/app/content/videoConvert.db'
VIDEO_DIRECTORY = '/Users/oomkaxena/Desktop/content/output'
# '/Users/oomkaxena/Desktop/content/output'
# '/app/content/output'

# Pagination settings
PER_PAGE = 3

@app.route('/')
def index():
    # Fetch all records from the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, original_file_name, converted_file_name, claim_number, ad_notes FROM converted_videos')
    all_videos = c.fetchall()
    conn.close()

    # Pagination logic
    page = request.args.get(get_page_parameter(), type=int) or 1
    offset = (page - 1) * PER_PAGE
    videos = all_videos[offset:offset+PER_PAGE]

    pagination = Pagination(
        page=page,
        per_page=PER_PAGE,
        total=len(all_videos),
        css_framework='bootstrap5',
        page_parameter='page'
    )

    # print(f"page={page}")
    # print(f"offset={offset}")
    # print(f"videos={videos}")
    # print(f"pagination.page={pagination.page}")
    # print(f"pagination.per_page={pagination.per_page}")
    # print(f"pagination.total={pagination.total}")

    total_pages = int(len(all_videos) / PER_PAGE) + (len(all_videos) % PER_PAGE != 0)
    current_page_range = list(range((page - 1) * PER_PAGE + 1, min(page * PER_PAGE, len(all_videos)) + 1))

    # print(f"total_pages={total_pages}")
    # print(f"current_page_range={current_page_range}")

    return render_template('index.html', videos=videos, pagination=pagination)

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
