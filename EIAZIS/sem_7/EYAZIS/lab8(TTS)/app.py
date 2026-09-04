import os
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import tts_engine

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'history.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

AUDIO_FOLDER = os.path.join(basedir, 'static', 'audio')
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

db = SQLAlchemy(app)


class SynthesisRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    voice_id = db.Column(db.String(200), nullable=False)
    rate = db.Column(db.Integer, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    audio_file = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Request {self.id}: {self.text[:20]}>'


@app.route('/', methods=['GET', 'POST'])
def index():
    voices = tts_engine.get_available_voices()
    audio_file_url = None
    error_message = None

    if not voices:
        error_message = "Не удалось найти голоса для синтеза речи. Проверьте системные настройки или перезапустите приложение."

    default_voice_id = voices[0].id if voices else ''
    form_data = {
        'text': 'Hello world! This is a test of the text to speech system.',
        'voice': default_voice_id,
        'rate': 150,
        'volume': 1.0
    }

    if request.method == 'POST' and voices:
        text = request.form.get('text', '')
        voice_id = request.form.get('voice')
        rate = int(request.form.get('rate', 150))
        volume = float(request.form.get('volume', 1.0))

        form_data = {'text': text, 'voice': voice_id, 'rate': rate, 'volume': volume}

        if text and voice_id is not None:
            filename = tts_engine.synthesize_speech(text, voice_id, rate, volume, AUDIO_FOLDER)

            if filename:
                audio_file_url = url_for('static', filename=f'audio/{filename}')
                new_request = SynthesisRequest(
                    text=text, voice_id=voice_id, rate=rate,
                    volume=volume, audio_file=filename
                )
                db.session.add(new_request)
                db.session.commit()

    return render_template('index.html', voices=voices, audio_file_url=audio_file_url, form_data=form_data,
                           error_message=error_message)

@app.route('/history')
def history():
    requests = SynthesisRequest.query.order_by(SynthesisRequest.timestamp.desc()).all()
    return render_template('history.html', requests=requests)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)