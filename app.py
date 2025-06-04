from flask import Flask, render_template, request, jsonify
import os
import whisper
from moviepy import AudioFileClip
from yt_dlp import YoutubeDL
import tempfile

app = Flask(__name__)
model = whisper.load_model("base")  # você pode trocar para "small", "medium" etc.

def transcrever_audio(path_audio):
    result = model.transcribe(path_audio, language='pt', fp16=False)
    return result['text']

def extrair_audio_de_video(path_video, path_audio):
    clip = AudioFileClip(path_video)
    clip.write_audiofile(path_audio, logger=None)
    clip.close()

def baixar_video(url, path_saida):
    ydl_opts = {
        'outtmpl': path_saida,
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transcrever/upload", methods=["POST"])
def transcrever_upload():
    if 'video' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        caminho_video = os.path.join(tmpdir, video_file.filename)
        video_file.save(caminho_video)
        caminho_audio = os.path.join(tmpdir, "audio.wav")

        extrair_audio_de_video(caminho_video, caminho_audio)
        texto = transcrever_audio(caminho_audio)

    return jsonify({"transcricao": texto})

@app.route("/transcrever/url", methods=["POST"])
def transcrever_url():
    data = request.json
    url_video = data.get("url")
    if not url_video:
        return jsonify({"error": "Nenhuma URL enviada"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        caminho_video = os.path.join(tmpdir, "video_baixado.mp4")
        try:
            baixar_video(url_video, caminho_video)
        except Exception as e:
            return jsonify({"error": f"Falha ao baixar vídeo: {str(e)}"}), 500
        
        caminho_audio = os.path.join(tmpdir, "audio.wav")
        extrair_audio_de_video(caminho_video, caminho_audio)
        texto = transcrever_audio(caminho_audio)

    return jsonify({"transcricao": texto})

if __name__ == "__main__":
    app.run(debug=True)
