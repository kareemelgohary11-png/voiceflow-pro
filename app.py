from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from gtts import gTTS
import tempfile
import os

app = Flask(__name__)
CORS(app)

VOICES = [
    {'name': 'ar', 'display': 'عربي', 'gender': 'Female', 'locale': 'ar'},
    {'name': 'ar-eg', 'display': 'عربي مصري', 'gender': 'Female', 'locale': 'ar'},
    {'name': 'ar-sa', 'display': 'عربي سعودي', 'gender': 'Female', 'locale': 'ar'},
    {'name': 'en', 'display': 'English', 'gender': 'Female', 'locale': 'en'},
    {'name': 'en-us', 'display': 'English US', 'gender': 'Female', 'locale': 'en'},
    {'name': 'en-gb', 'display': 'English UK', 'gender': 'Female', 'locale': 'en'},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voices')
def get_voices():
    return jsonify(VOICES)

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text', '').strip()
    voice = data.get('voice', 'ar')

    if not text:
        return jsonify({'error': 'لا يوجد نص'}), 400
    if len(text) > 3000:
        return jsonify({'error': 'النص طويل جداً'}), 400

    try:
        lang = voice if len(voice) == 2 else voice[:2]
        tts = gTTS(text=text, lang=lang, slow=False)
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp_path = tmp.name
        tmp.close()
        tts.save(tmp_path)
        return send_file(tmp_path, mimetype='audio/mpeg', as_attachment=True, download_name='voiceflow.mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
