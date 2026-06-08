from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)
CORS(app)

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voices')
def get_voices():
    try:
        voices = run_async(edge_tts.list_voices())
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': 'النص طويل جداً'}), 400

    async def generate():
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmp_path = f.name
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(tmp_path)
        return tmp_path

    try:
        tmp_path = run_async(generate())
        return send_file(tmp_path, mimetype='audio/mpeg', as_attachment=True, download_name='voiceflow.mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
