import os
import uuid
import datetime
import speech_recognition as sr
from pydub import AudioSegment
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

import subprocess
import webbrowser
import platform

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
AUDIO_FOLDER = os.path.join(BASE_DIR, 'static', 'audio')
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'speech_queries.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = AUDIO_FOLDER

db = SQLAlchemy(app)

COMMAND_LIST = {
    "open browser": "Keywords: 'browser', 'google', 'internet'",
    "open notepad": "Keywords: 'notepad' + 'open/start/run'",
    "open calculator": "Keywords: 'calculator' + 'open/start/run'",
    "open command line": "Keywords: 'command', 'terminal', 'cmd'",
    "open explorer": "Keywords: 'explorer' + 'open/show'",
    "time": "Keywords: 'time'"
}

class SpeechQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    command_executed = db.Column(db.String(200), nullable=True)


with app.app_context():
    db.create_all()


def is_command_triggered(text, targets, actions=["open", "start", "launch", "run", "show"]):

    found_target = any(t in text for t in targets)
    found_action = any(a in text for a in actions)
    return found_target and found_action


def execute_voice_command(text):

    text = text.lower()
    executed_actions = []

    try:
        if is_command_triggered(text, ["browser", "google", "internet", "chrome"]):
            webbrowser.open("https://www.google.com")
            executed_actions.append("Action: Opened Web Browser")

        if is_command_triggered(text, ["notepad", "editor"]):
            if platform.system() == "Windows":
                subprocess.Popen(["notepad.exe"])
                executed_actions.append("Action: Opened Notepad")
            else:
                executed_actions.append("Error: Notepad is Windows only")

        if is_command_triggered(text, ["calculator", "calc"]):
            if platform.system() == "Windows":
                subprocess.Popen("calc.exe")
                executed_actions.append("Action: Opened Calculator")
            else:
                executed_actions.append("Error: Calculator is Windows only")

        if is_command_triggered(text, ["command", "cmd", "terminal", "powershell"]):
            if platform.system() == "Windows":
                subprocess.Popen("start cmd", shell=True)
                executed_actions.append("Action: Opened Command Prompt")

        if is_command_triggered(text, ["explorer", "folder", "files"]):
            if platform.system() == "Windows":
                subprocess.Popen("explorer")
                executed_actions.append("Action: Opened File Explorer")

        if "time" in text:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            executed_actions.append(f"Action: Current time is {now}")

    except Exception as e:
        executed_actions.append(f"Command Error: {str(e)}")

    if not executed_actions:
        return None

    return " | ".join(executed_actions)


def process_audio_file(file_storage, source_type):

    recognizer = sr.Recognizer()
    unique_name = str(uuid.uuid4())
    final_filename = f"{unique_name}.wav"
    final_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{unique_name}")

    try:
        file_storage.save(temp_path)
        sound = AudioSegment.from_file(temp_path)
        sound = sound.set_channels(1)
        sound.export(final_path, format="wav")

        text_result = ""
        with sr.AudioFile(final_path) as source:
            audio_data = recognizer.record(source)
            try:
                text_result = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                text_result = "[Unintelligible / No Speech Detected]"
            except sr.RequestError:
                text_result = "[Error: Speech Service Unavailable]"

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return text_result, final_filename

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return f"System Error: {str(e)}", None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file_upload' not in request.files:
            return redirect(request.url)

        file = request.files['file_upload']
        if file.filename == '':
            return redirect(request.url)

        if file:
            text, saved_filename = process_audio_file(file, 'upload')

            if saved_filename:
                cmd_status = execute_voice_command(text)

                new_query = SpeechQuery(
                    text=text,
                    filename=saved_filename,
                    command_executed=cmd_status
                )
                db.session.add(new_query)
                db.session.commit()

                display_text = text
                if cmd_status:
                    display_text += f"\n\n[{cmd_status}]"

                return render_template('index.html', result=display_text, audio_file=saved_filename,
                                       commands=COMMAND_LIST)
            else:
                return render_template('index.html', error=text, commands=COMMAND_LIST)

    return render_template('index.html', commands=COMMAND_LIST)


@app.route('/upload_mic', methods=['POST'])
def upload_mic():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'No audio data'}), 400

    file = request.files['audio_data']
    text, saved_filename = process_audio_file(file, 'mic')

    if saved_filename:
        cmd_status = execute_voice_command(text)

        new_query = SpeechQuery(
            text=text,
            filename=saved_filename,
            command_executed=cmd_status
        )
        db.session.add(new_query)
        db.session.commit()

        display_text = text
        if cmd_status:
            display_text += f"\n\n[{cmd_status}]"

        audio_url = url_for('static', filename='audio/' + saved_filename)
        return jsonify({'text': display_text, 'audio_url': audio_url})
    else:
        return jsonify({'error': text})


@app.route('/history')
def history():
    queries = SpeechQuery.query.order_by(SpeechQuery.timestamp.desc()).all()
    return render_template('history.html', queries=queries)


@app.route('/help')
def help_page():
    return render_template('help.html', commands=COMMAND_LIST)


if __name__ == '__main__':
    app.run(debug=True, port=5012)