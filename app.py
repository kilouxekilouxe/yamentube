from flask import Flask, request, send_file, jsonify, render_template
from yt_dlp import YoutubeDL
import os
import uuid

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'

# Ensure download directory exists
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

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

    # Generate a unique ID for this download
    download_id = str(uuid.uuid4())
    
    # Set format based on quality
    if quality == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f"{app.config['DOWNLOAD_FOLDER']}/{download_id}/%(title)s.%(ext)s",
            'quiet': True,
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            'merge_output_format': 'mp4',
            'outtmpl': f"{app.config['DOWNLOAD_FOLDER']}/{download_id}/%(title)s.%(ext)s",
            'quiet': True,
        }

    try:
        # Ensure the download subdirectory exists
        os.makedirs(f"{app.config['DOWNLOAD_FOLDER']}/{download_id}", exist_ok=True)
        
        # Extract info and download
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Adjust extension for mp3
            if quality == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            # Get just the filename without the path
            title = os.path.basename(filename)
            
            # Return download info
            return jsonify({
                "success": True,
                "download_id": download_id,
                "filename": title
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_file/<download_id>/<filename>', methods=['GET'])
def get_file(download_id, filename):
    try:
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], download_id, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "الملف غير موجود"}), 404
            
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Schedule cleanup after a delay using a background task
        # For simplicity, we'll remove files immediately, but in production
        # you might want to use a task queue like Celery for delayed cleanup
        try:
            folder_path = os.path.join(app.config['DOWNLOAD_FOLDER'], download_id)
            for file in os.listdir(folder_path):
                os.remove(os.path.join(folder_path, file))
            os.rmdir(folder_path)
        except:
            pass  # Ignore cleanup errors

if __name__ == '__main__':
    app.run(debug=True)
