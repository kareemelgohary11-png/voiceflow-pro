from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import subprocess
import tempfile
import os
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voices')
def get_voices():
    try:
        result = subprocess.run(
            ['python', '-c', 'import asyncio; import edge_tts; import json; voices = asyncio.run(edge_tts.list_voices()); print(json.dumps(voices))'],
            capture_output=True, text=True, timeout=30
        )
        voices = json.loads(result.stdout)
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

    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp_path = tmp.name
        tmp.close()

        script = f"""
import asyncio
import edge_tts
async def main():
    c = edge_tts.Communicate({repr(text)}, {repr(voice)}, rate={repr(rate)}, pitch={repr(pitch)})
    await c.save({repr(tmp_path)})
asyncio.run(main())
"""
        result = subprocess.run(
            ['python', '-c', script],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            return jsonify({'error': result.stderr}), 500

        return send_file(tmp_path, mimetype='audio/mpeg', as_attachment=True, download_name='voiceflow.mp3')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
