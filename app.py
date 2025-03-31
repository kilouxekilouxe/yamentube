from flask import Flask, request, send_file, jsonify, render_template
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    data = request.form
    url = data.get('youtube_url')
    quality = data.get('quality', 'mp3')

    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        return jsonify({"error": "رابط غير صالح!"}), 400

    ydl_opts = {
        'format': 'bestaudio/best' if quality == 'mp3' else f'bestvideo[height<={quality}]+bestaudio',
        'outtmpl': f"{app.config['DOWNLOAD_FOLDER']}/%(title)s.%(ext)s",
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'filename' in locals():
            os.remove(filename)


if __name__ == '__main__':
    app.run(debug=True)
