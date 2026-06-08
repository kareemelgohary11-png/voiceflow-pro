from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voices')
def get_voices():
    async def fetch():
        return await edge_tts.list_voices()
    voices = asyncio.run(fetch())
    filtered = [
        {
            'name': v['ShortName'],
            'display': v['FriendlyName'],
            'gender': v['Gender'],
            'locale': v['Locale']
        }
        for v in voices
        if v['Locale'].startswith('ar') or v['Locale'].startswith('en')
    ]
    return jsonify(filtered)

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text', '').strip()
    voice = data.get('voice', 'ar-EG-SalmaNeural')
    rate = data.get('rate', '+0%')
    pitch = data.get('pitch', '+0Hz')

    if not text:
        return jsonify({'error': 'لا يوجد نص'}), 400
    if len(text) > 3000:
        return jsonify({'error': 'النص طويل جداً، الحد الأقصى 3000 حرف'}), 400

    async def generate():
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmp_path = f.name
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(tmp_path)
        return tmp_path

    try:
        tmp_path = asyncio.run(generate())
        return send_file(tmp_path, mimetype='audio/mpeg', as_attachment=True, download_name='voiceflow.mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
