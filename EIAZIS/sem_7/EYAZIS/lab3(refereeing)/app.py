from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
import os
from werkzeug.utils import secure_filename
import io
import json
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import uuid
import re

from file_processor import read_file
from summarizer import TextSummarizer

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем временные папки
UPLOAD_FOLDER = 'uploads'
TEXT_STORAGE_FOLDER = 'text_storage'
SUMMARY_STORAGE_FOLDER = 'summary_storage'
HISTORY_FILE = 'summarization_history.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEXT_STORAGE_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_STORAGE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEXT_STORAGE_FOLDER'] = TEXT_STORAGE_FOLDER
app.config['SUMMARY_STORAGE_FOLDER'] = SUMMARY_STORAGE_FOLDER

# Инициализация суммаризатора
summarizer = TextSummarizer()

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'txt'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def split_summary_into_lines(summary_text, language='ru'):
    """
    Разбивает текст реферата на отдельные предложения для отображения с новой строки
    """
    if not summary_text:
        return []

    # Разбиваем текст на предложения
    if language == 'ru':
        # Для русского языка: разделители .!? с последующим пробелом или концом строки
        sentences = re.split(r'(?<=[.!?])\s+', summary_text)
    else:
        # Для английского языка
        sentences = re.split(r'(?<=[.!?])\s+', summary_text)

    # Убираем пустые строки и лишние пробелы
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    return sentences


def load_history():
    """Загружает историю реферирования из JSON файла"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
    return []


def save_history(history):
    """Сохраняет историю реферирования в JSON файл"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")


def save_text_to_file(text, text_id):
    """Сохраняет текст во временный файл"""
    try:
        file_path = os.path.join(app.config['TEXT_STORAGE_FOLDER'], f"{text_id}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return file_path
    except Exception as e:
        print(f"Error saving text: {e}")
        return None


def load_text_from_file(text_id):
    """Загружает текст из временного файла"""
    try:
        file_path = os.path.join(app.config['TEXT_STORAGE_FOLDER'], f"{text_id}.txt")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error loading text: {e}")
    return None


def save_summary_data(summary_id, classic_summary, semantic_summary, keyword_summary, semantic_keywords,
                      semantic_analysis="", key_points=None):
    """Сохраняет данные реферата в отдельный файл"""
    try:
        file_path = os.path.join(app.config['SUMMARY_STORAGE_FOLDER'], f"{summary_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'classic_summary': classic_summary,
                'semantic_summary': semantic_summary,
                'keyword_summary': keyword_summary,
                'semantic_keywords': semantic_keywords or [],
                'semantic_analysis': semantic_analysis or "",
                'key_points': key_points or []
            }, f, ensure_ascii=False, indent=2)
        return file_path
    except Exception as e:
        print(f"Error saving summary: {e}")
        return None


def load_summary_data(summary_id):
    """Загружает данные реферата из файла"""
    try:
        file_path = os.path.join(app.config['SUMMARY_STORAGE_FOLDER'], f"{summary_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading summary: {e}")
    return None


def cleanup_old_files(hours=24):
    """Очищает старые временные файлы"""
    try:
        current_time = datetime.now().timestamp()
        # Очищаем текстовые файлы
        for folder in [app.config['TEXT_STORAGE_FOLDER'], app.config['SUMMARY_STORAGE_FOLDER']]:
            for filename in os.listdir(folder):
                if filename.endswith(('.txt', '.json')):
                    file_path = os.path.join(folder, filename)
                    if os.path.exists(file_path):
                        file_time = os.path.getctime(file_path)
                        if current_time - file_time > hours * 3600:
                            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up files: {e}")


def add_to_history(result_data):
    """Добавляет запись в историю"""
    history = load_history()

    # Ограничиваем историю последними 50 записями
    if len(history) >= 50:
        history = history[-49:]

    # Сохраняем полный текст в отдельный файл
    text_id = str(uuid.uuid4())
    save_text_to_file(result_data.get('full_text', ''), text_id)

    # Сохраняем данные реферата в отдельный файл
    summary_id = str(uuid.uuid4())
    save_summary_data(
        summary_id,
        result_data.get('classic_summary', ''),
        result_data.get('semantic_summary', ''),
        result_data.get('keyword_summary', []),
        result_data.get('semantic_keywords', []),
        result_data.get('semantic_analysis', ''),
        result_data.get('key_points', [])
    )

    history.append({
        'id': len(history) + 1,
        'text_id': text_id,
        'summary_id': summary_id,
        'timestamp': datetime.now().isoformat(),
        'filename': result_data.get('filename', ''),
        'language': result_data.get('language', ''),
        'original_length': result_data.get('original_length', 0),
        'summary_length': result_data.get('summary_length', 0),
        'semantic_summary_length': result_data.get('semantic_summary_length', 0),
        'compression_ratio': result_data.get('compression_ratio', 0),
        'semantic_compression_ratio': result_data.get('semantic_compression_ratio', 0),
        'classic_summary_preview': result_data.get('classic_summary', '')[:100] + '...' if len(
            result_data.get('classic_summary', '')) > 100 else result_data.get('classic_summary', ''),
        'semantic_summary_preview': result_data.get('semantic_summary', '')[:100] + '...' if len(
            result_data.get('semantic_summary', '')) > 100 else result_data.get('semantic_summary', ''),
        'keyword_count': len(result_data.get('keyword_summary', [])),
        'semantic_keyword_count': len(result_data.get('semantic_keywords', [])),
        'has_full_text': True
    })

    save_history(history)
    cleanup_old_files()


@app.route('/')
def index():
    """Главная страница с формой загрузки"""
    return render_template('index.html')


@app.route('/help')
def help_page():
    """Страница помощи"""
    return render_template('help.html')


@app.route('/history')
def history_page():
    """Страница истории реферирования"""
    history = load_history()
    # Сортируем историю по ID в обратном порядке (новые сверху)
    history.sort(key=lambda x: x['id'], reverse=True)
    return render_template('history.html', history=history)


@app.route('/history/clear', methods=['POST'])
def clear_history():
    """Очистка истории"""
    try:
        for folder in [app.config['TEXT_STORAGE_FOLDER'], app.config['SUMMARY_STORAGE_FOLDER']]:
            for filename in os.listdir(folder):
                if filename.endswith(('.txt', '.json')):
                    file_path = os.path.join(folder, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
    except Exception as e:
        print(f"Error clearing files: {e}")

    save_history([])
    flash('История очищена')
    return redirect(url_for('history_page'))


@app.route('/history/view/<int:history_id>')
def view_history_item(history_id):
    """Просмотр конкретного элемента истории"""
    history = load_history()
    item = next((item for item in history if item['id'] == history_id), None)

    if item:
        # Загружаем полный текст из файла
        full_text = load_text_from_file(item.get('text_id', ''))

        # Загружаем данные реферата из файла
        summary_data = load_summary_data(item.get('summary_id', ''))

        if summary_data:
            classic_summary = summary_data.get('classic_summary', 'Нет данных')
            semantic_summary = summary_data.get('semantic_summary', 'Нет данных')
            keyword_summary = summary_data.get('keyword_summary', [])
            semantic_keywords = summary_data.get('semantic_keywords', [])
            semantic_analysis = summary_data.get('semantic_analysis', '')
            key_points = summary_data.get('key_points', [])
        else:
            classic_summary = 'Данные реферата не найдены'
            semantic_summary = 'Данные реферата не найдены'
            keyword_summary = []
            semantic_keywords = []
            semantic_analysis = ''
            key_points = []

        # Разбиваем рефераты на предложения для отображения
        classic_summary_sentences = split_summary_into_lines(classic_summary, item.get('language', 'ru'))
        semantic_summary_sentences = split_summary_into_lines(semantic_summary, item.get('language', 'ru'))

        # Вычисляем compression ratio если его нет в старых записях
        original_length = item.get('original_length', 0)
        semantic_summary_length = item.get('semantic_summary_length', len(semantic_summary))
        semantic_compression_ratio = item.get('semantic_compression_ratio', 0)

        # Если semantic_compression_ratio не был сохранен, вычисляем его
        if semantic_compression_ratio == 0 and original_length > 0 and semantic_summary_length > 0:
            semantic_compression_ratio = round((1 - semantic_summary_length / original_length) * 100, 2)

        result_data = {
            'filename': item.get('filename', ''),
            'language': item.get('language', ''),
            'original_length': original_length,
            'summary_length': item.get('summary_length', 0),
            'semantic_summary_length': semantic_summary_length,
            'compression_ratio': item.get('compression_ratio', 0),
            'semantic_compression_ratio': semantic_compression_ratio,
            'classic_summary': classic_summary,
            'classic_summary_sentences': classic_summary_sentences,
            'semantic_summary': semantic_summary,
            'semantic_summary_sentences': semantic_summary_sentences,
            'keyword_summary': keyword_summary,
            'semantic_keywords': semantic_keywords,
            'semantic_analysis': semantic_analysis,
            'key_points': key_points,
            'file_size': item.get('original_length', 0),
            'original_text_preview': full_text[:500] + '...' if full_text and len(full_text) > 500 else full_text,
            'full_text': full_text,
            'upload_time': item.get('timestamp', ''),
            'text_id': item.get('text_id', '')
        }

        return render_template('result.html', result=result_data, from_history=True)
    else:
        flash('Запись не найдена')
        return redirect(url_for('history_page'))


@app.route('/upload', methods=['POST'])
def upload_file():
    """Обработка загруженного файла"""
    if 'file' not in request.files:
        flash('Файл не выбран')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('Файл не выбран')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        try:
            # Сохраняем файл
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Обрабатываем файл
            file_info = read_file(file_path)

            # Показываем сообщение о начале обработки
            flash('Начинаем обработку текста с использованием AI... Это может занять несколько минут.')

            # Генерируем реферат с использованием всех методов
            summary_result = summarizer.create_summary(
                file_info['text'],
                file_info['language']
            )

            # Разбиваем рефераты на предложения для отображения
            classic_summary_sentences = split_summary_into_lines(
                summary_result.get('classic_summary', ''),
                file_info['language']
            )

            semantic_summary_sentences = split_summary_into_lines(
                summary_result.get('semantic_summary', ''),
                file_info['language']
            )

            # Сохраняем результаты
            summary_result['filename'] = filename
            summary_result['file_size'] = os.path.getsize(file_path)
            summary_result['original_text_preview'] = file_info['text'][:500] + '...' if len(
                file_info['text']) > 500 else file_info['text']
            summary_result['full_text'] = file_info['text']
            summary_result['upload_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_result['text_id'] = str(uuid.uuid4())
            summary_result['classic_summary_sentences'] = classic_summary_sentences
            summary_result['semantic_summary_sentences'] = semantic_summary_sentences

            # Сохраняем полный текст в отдельный файл
            save_text_to_file(file_info['text'], summary_result['text_id'])

            # Добавляем в историю
            add_to_history(summary_result)

            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)

            flash('Обработка завершена успешно!')
            return render_template('result.html', result=summary_result)

        except Exception as e:
            flash(f'Ошибка обработки файла: {str(e)}')
            return redirect(url_for('index'))

    else:
        flash('Неподдерживаемый формат файла. Разрешены только TXT файлы.')
        return redirect(url_for('index'))


@app.route('/view_full_text')
def view_full_text():
    """Просмотр полного текста исходного документа"""
    text_id = request.args.get('text_id', '')
    filename = request.args.get('filename', 'document.txt')

    if text_id:
        full_text = load_text_from_file(text_id)
        if full_text:
            return render_template('full_text.html', full_text=full_text, filename=filename)

    flash('Текст не найден')
    return redirect(url_for('index'))


@app.route('/get_full_text/<text_id>')
def get_full_text(text_id):
    """API для получения полного текста по ID"""
    full_text = load_text_from_file(text_id)
    if full_text:
        return jsonify({'success': True, 'text': full_text})
    else:
        return jsonify({'success': False, 'error': 'Text not found'})


@app.route('/download/<format_type>')
def download_summary(format_type):
    """Скачивание результатов в выбранном формате"""
    try:
        text_id = request.args.get('text_id', '')

        if not text_id:
            flash('ID текста не указан')
            return redirect(url_for('index'))

        # Загружаем данные реферата из истории или временного хранилища
        summary_data = None

        # Сначала ищем в истории
        history = load_history()
        for item in history:
            if item.get('text_id') == text_id:
                summary_data = load_summary_data(item.get('summary_id', ''))
                break

        if not summary_data:
            flash('Данные реферата не найдены')
            return redirect(url_for('index'))

        classic_summary = summary_data.get('classic_summary', '')
        semantic_summary = summary_data.get('semantic_summary', '')
        keyword_summary = summary_data.get('keyword_summary', [])
        semantic_keywords = summary_data.get('semantic_keywords', [])

        if format_type == 'txt':
            output = io.StringIO()
            output.write("АВТОМАТИЧЕСКИЙ РЕФЕРАТ ДОКУМЕНТА\n")
            output.write("=" * 50 + "\n\n")

            output.write("СЕМАНТИЧЕСКИЙ РЕФЕРАТ (AI):\n\n")
            semantic_sentences = split_summary_into_lines(semantic_summary)
            for sentence in semantic_sentences:
                output.write(f"• {sentence}\n")

            output.write("\n" + "=" * 50 + "\n\n")
            output.write("КЛАССИЧЕСКИЙ РЕФЕРАТ:\n\n")
            classic_sentences = split_summary_into_lines(classic_summary)
            for sentence in classic_sentences:
                output.write(f"• {sentence}\n")

            output.write("\nКЛЮЧЕВЫЕ СЛОВА:\n")
            output.write("Семантические: " + ", ".join(semantic_keywords) + "\n")
            output.write("Статистические: " + ", ".join(keyword_summary) + "\n\n")
            output.write("=" * 50 + "\n")
            output.write(f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            mem = io.BytesIO()
            mem.write(output.getvalue().encode('utf-8'))
            mem.seek(0)

            return send_file(
                mem,
                as_attachment=True,
                download_name='summary.txt',
                mimetype='text/plain'
            )

        elif format_type == 'pdf':
            # Создаем PDF файл
            mem = io.BytesIO()
            p = canvas.Canvas(mem, pagesize=A4)

            y_position = 800
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, y_position, "АВТОМАТИЧЕСКИЙ РЕФЕРАТ ДОКУМЕНТА")
            y_position -= 40

            # Семантический реферат
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y_position, "Семантический реферат (AI):")
            y_position -= 25

            p.setFont("Helvetica", 10)
            semantic_sentences = split_summary_into_lines(semantic_summary)
            for sentence in semantic_sentences:
                bullet_text = f"• {sentence}"
                words = bullet_text.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if len(test_line) > 80:
                        p.drawString(100, y_position, line)
                        y_position -= 15
                        line = word + " "
                        if y_position < 50:
                            p.showPage()
                            y_position = 800
                            p.setFont("Helvetica", 10)
                    else:
                        line = test_line

                if line:
                    p.drawString(100, y_position, line)
                    y_position -= 20

                if y_position < 100:
                    p.showPage()
                    y_position = 800
                    p.setFont("Helvetica", 10)

            y_position -= 20

            # Классический реферат
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y_position, "Классический реферат:")
            y_position -= 25

            p.setFont("Helvetica", 10)
            classic_sentences = split_summary_into_lines(classic_summary)
            for sentence in classic_sentences:
                bullet_text = f"• {sentence}"
                words = bullet_text.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if len(test_line) > 80:
                        p.drawString(100, y_position, line)
                        y_position -= 15
                        line = word + " "
                        if y_position < 50:
                            p.showPage()
                            y_position = 800
                            p.setFont("Helvetica", 10)
                    else:
                        line = test_line

                if line:
                    p.drawString(100, y_position, line)
                    y_position -= 20

                if y_position < 100:
                    p.showPage()
                    y_position = 800
                    p.setFont("Helvetica", 10)

            y_position -= 20

            # Ключевые слова
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y_position, "Ключевые слова:")
            y_position -= 20

            p.setFont("Helvetica", 10)
            semantic_keywords_text = "Семантические: " + ", ".join(semantic_keywords[:10])
            classic_keywords_text = "Статистические: " + ", ".join(keyword_summary[:10])

            # Обрабатываем семантические ключевые слова
            words = semantic_keywords_text.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if len(test_line) > 80:
                    p.drawString(100, y_position, line)
                    y_position -= 15
                    line = word + " "
                    if y_position < 50:
                        p.showPage()
                        y_position = 800
                        p.setFont("Helvetica", 10)
                else:
                    line = test_line

            if line:
                p.drawString(100, y_position, line)
                y_position -= 15

            # Обрабатываем статистические ключевые слова
            words = classic_keywords_text.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if len(test_line) > 80:
                    p.drawString(100, y_position, line)
                    y_position -= 15
                    line = word + " "
                    if y_position < 50:
                        p.showPage()
                        y_position = 800
                        p.setFont("Helvetica", 10)
                else:
                    line = test_line

            if line:
                p.drawString(100, y_position, line)

            # Добавляем информацию о модели
            y_position -= 30
            p.setFont("Helvetica-Oblique", 8)
            p.drawString(100, y_position, f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            y_position -= 12
            p.drawString(100, y_position, "Использована модель: Llama 3.2 через Ollama")

            p.showPage()
            p.save()
            mem.seek(0)

            return send_file(
                mem,
                as_attachment=True,
                download_name='summary.pdf',
                mimetype='application/pdf'
            )

        flash('Неподдерживаемый формат для скачивания')
        return redirect(url_for('index'))

    except Exception as e:
        flash(f'Ошибка при создании файла: {str(e)}')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, threaded=True)