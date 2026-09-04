import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, send_from_directory
from werkzeug.utils import secure_filename
import tempfile

# Импорт вашего сервиса обработки
from LanguageDetector import LanguageDetectionService, DetectionResult

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Замените на случайный ключ

# Конфигурация
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
HISTORY_FILE = 'history.json'
ALLOWED_EXTENSIONS = {'html', 'htm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file

# Создание папок если их нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Инициализация сервиса (замените на вашу реальную конфигурацию)
DB_CONFIG = {
    'host': 'localhost',
    'database': 'lang_detection',
    'user': 'postgres',
    'password': '1234'
}

# Инициализация детекторов (замените на ваши реальные детекторы)
try:
    # Эти импорты нужно заменить на ваши реальные модули
    from build_profile_ngram import NGramProfileBuilder
    from build_profiles_for_alphabet_alg import AlphabeticalProfileBuilder
    from Neural_lang_detector import load_trained_model

    alphabetical_detector = AlphabeticalProfileBuilder(None)
    ngram_detector = NGramProfileBuilder(None)
    neural_detector = load_trained_model('trained_model.pth', 'vocabulary.pkl')

    detection_service = LanguageDetectionService(
        db_config=DB_CONFIG,
        alphabetical_detector_=alphabetical_detector,
        ngram_detector_=ngram_detector,
        neural_detector_=neural_detector
    )
except ImportError as e:
    print(f"Warning: Could not initialize detection service: {e}")
    detection_service = None


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_to_history(file_info, results):
    """Сохраняет информацию о обработке в историю"""
    # Убедимся, что results имеет правильную структуру
    if isinstance(results, dict) and 'results' in results and 'summary' in results:
        processed_results = results
    else:
        # Если results пришел в неправильном формате, создаем базовую структуру
        processed_results = {
            'results': [],
            'summary': {
                'total_methods': 0,
                'successful_detections': 0,
                'languages_detected': [],
                'average_confidence': 0.0,
                'fastest_method': None
            }
        }

    history_entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'filename': file_info['filename'],
        'original_filename': file_info['original_filename'],
        'file_path': file_info['file_path'],
        'results': processed_results
    }

    # Загрузка существующей истории
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    # Добавление новой записи
    history.insert(0, history_entry)

    # Сохранение обратно в файл
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return history_entry['id']


def load_history():
    """Загружает историю из файла"""
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_results_to_file(results, filename):
    """Сохраняет результаты в JSON файл"""
    results_file = os.path.join(app.config['RESULTS_FOLDER'], f"{filename}_results.json")

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results_file


@app.route('/')
def index():
    """Главная страница - загрузка файла"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Обработка загруженного файла"""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Сохранение файла
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Обработка файла
        try:
            if detection_service is None:
                flash('Detection service is not available', 'danger')
                return redirect(url_for('index'))

            results = detection_service.detect_from_html_file(file_path)
            summary = detection_service.get_detection_summary(results)

            # Конвертация результатов в словари для JSON
            results_dict = [result.__dict__ for result in results]
            summary_dict = summary

            # Сохранение в историю
            file_info = {
                'filename': unique_filename,
                'original_filename': filename,
                'file_path': file_path
            }
            history_id = save_to_history(file_info, {
                'results': results_dict,
                'summary': summary_dict
            })

            # Перенаправление на страницу результатов
            return redirect(url_for('results', file_id=history_id))

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('index'))

    flash('Invalid file type. Please upload HTML files only.', 'danger')
    return redirect(url_for('index'))


@app.route('/results/<file_id>')
def results(file_id):
    """Страница результатов обработки"""
    # Поиск в истории
    history = load_history()
    entry = next((item for item in history if item['id'] == file_id), None)

    if not entry:
        flash('Results not found', 'danger')
        return redirect(url_for('index'))

    # Получаем информацию о файле
    file_exists = False
    file_size = 0
    if entry.get('file_path') and os.path.exists(entry['file_path']):
        file_exists = True
        file_size = os.path.getsize(entry['file_path'])

    return render_template('results.html',
                           entry=entry,
                           file_id=file_id,
                           file_exists=file_exists,
                           file_size=file_size)


@app.route('/download/<file_id>')
def download_file(file_id):
    """Скачивание оригинального файла"""
    history = load_history()
    entry = next((item for item in history if item['id'] == file_id), None)

    if not entry or not os.path.exists(entry['file_path']):
        flash('File not found', 'danger')
        return redirect(url_for('index'))

    return send_file(entry['file_path'],
                     as_attachment=True,
                     download_name=entry['original_filename'])


@app.route('/view/<file_id>')
def view_file(file_id):
    """Просмотр HTML файла в браузере"""
    history = load_history()
    entry = next((item for item in history if item['id'] == file_id), None)

    if not entry or not os.path.exists(entry['file_path']):
        flash('File not found', 'danger')
        return redirect(url_for('index'))

    return send_file(entry['file_path'])


@app.route('/save_results/<file_id>')
def save_results(file_id):
    """Сохранение результатов в файл"""
    history = load_history()
    entry = next((item for item in history if item['id'] == file_id), None)

    if not entry:
        flash('Results not found', 'danger')
        return redirect(url_for('index'))

    try:
        results_file = save_results_to_file(entry['results'], file_id)
        return send_file(results_file,
                         as_attachment=True,
                         download_name=f"results_{file_id}.json")
    except Exception as e:
        flash(f'Error saving results: {str(e)}', 'danger')
        return redirect(url_for('results', file_id=file_id))


@app.route('/history')
def history():
    """Страница истории обработки"""
    history_data = load_history()
    return render_template('history.html', history=history_data)


@app.route('/help')
def help_page():
    """Страница помощи"""
    return render_template('help.html')


if __name__ == '__main__':
    app.run(debug=True)