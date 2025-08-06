from flask import Flask, request, render_template, redirect, url_for
import sqlite3, os, time
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, DATABASE, USE_S3
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    videos = conn.execute('SELECT * FROM videos ORDER BY upload_time DESC').fetchall()
    conn.close()
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)

            # Convert to MP4 with ffmpeg
            mp4_path = os.path.splitext(path)[0] + ".mp4"
            subprocess.run(['ffmpeg', '-i', path, '-vcodec', 'libx264', '-acodec', 'aac', mp4_path])
            os.remove(path)  # Remove original file

            conn = get_db_connection()
            conn.execute('INSERT INTO videos (title, filename) VALUES (?, ?)', (title, os.path.basename(mp4_path)))
            conn.commit()
            conn.close()

            return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/watch/<int:video_id>')
def watch(video_id):
    conn = get_db_connection()
    video = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    conn.close()
    if video is None:
        return "Video not found", 404
    return render_template('watch.html', video=video)

