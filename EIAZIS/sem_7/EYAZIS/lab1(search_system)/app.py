import logging
import os
from search_service import SearchService
from file_watcher import FileWatcher
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort, send_file
from werkzeug.utils import secure_filename

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'search_system'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
}

WATCH_DIRECTORY = os.getenv(
    'WATCH_DIRECTORY',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'documents'),
)

app = Flask(__name__, template_folder='documents/templates')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

search_service = None
file_watcher = None


@app.context_processor
def inject_globals():
    return dict(
        search_service=search_service,
        WATCH_DIRECTORY=WATCH_DIRECTORY
    )


@app.route('/')
def index():
    """Главная страница с поиском"""
    stats = {}
    if search_service:
        try:
            stats['total_docs'] = search_service.data_service.get_document_count()
            stats['avg_doc_length'] = search_service.data_service.get_avg_doc_length()
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            stats['total_docs'] = 0
            stats['avg_doc_length'] = 0
    else:
        stats['total_docs'] = 0
        stats['avg_doc_length'] = 0

    return render_template('index.html', stats=stats)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Страница поиска"""
    if request.method == 'POST':
        query = request.form.get('query', '')
        top_k = int(request.form.get('top_k', 10))

        if not query:
            return render_template('search.html', error='Please enter a search query')

        search_response = search_service.search_with_gpt_fallback(query, top_k)

        return render_template('search.html',
                               query=query,
                               search_response=search_response,
                               results_count=len(search_response['results']))

    return render_template('search.html')


@app.route('/metrics', methods=['GET', 'POST'])
def metrics():
    """Страница расчета метрик качества"""
    if request.method == 'POST':
        query = request.form.get('query', '')
        relevant_docs_text = request.form.get('relevant_docs', '')

        if not query:
            return render_template('metrics.html', error='Please enter a query')

        relevant_docs = [doc.strip() for doc in relevant_docs_text.split('\n') if doc.strip()]

        metrics_result = search_service.calculate_metrics(query, relevant_docs)
        return render_template('metrics.html',
                               metrics=metrics_result,
                               relevant_docs_text=relevant_docs_text)

    return render_template('metrics.html')


@app.route('/documents')
def documents():
    """Страница управления документами"""
    docs = search_service.data_service.get_all_documents()
    documents_info = []

    for doc_id, file_path, last_modified in docs:
        doc_details = search_service.data_service.get_document_by_path(file_path)
        if doc_details:
            documents_info.append({
                'id': doc_id,
                'title': doc_details['title'],
                'file_path': file_path,
                'date_added': doc_details['date_added'],
                'last_modified': doc_details['last_modified'],
                'doc_length': doc_details['doc_length']
            })

    return render_template('documents.html', documents=documents_info)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Страница загрузки и индексирования документов"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', error='No file selected')

        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', error='No file selected')

        if file and file.filename.endswith('.txt'):
            try:
                # Ensure directory exists
                os.makedirs(WATCH_DIRECTORY, exist_ok=True)

                # Create safe file path
                filename = secure_filename(file.filename)
                file_path = os.path.join(WATCH_DIRECTORY, filename)

                # Check if file already exists
                if os.path.exists(file_path):
                    return render_template('upload.html',
                                           error=f'File {filename} already exists')

                # Save file
                file.save(file_path)
                logging.info(f"File saved to: {file_path}")

                # Index file
                success = search_service.index_file(file_path)

                if success:
                    return render_template('upload.html',
                                           success=f'File {filename} successfully indexed')
                else:
                    # Clean up if indexing failed
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return render_template('upload.html',
                                           error=f'Failed to index file {filename}')

            except Exception as e:
                logging.error(f"Upload error: {e}")
                # Clean up on error
                file_path = os.path.join(WATCH_DIRECTORY, secure_filename(file.filename))
                if os.path.exists(file_path):
                    os.remove(file_path)
                return render_template('upload.html',
                                       error=f'Error during upload: {str(e)}')

        else:
            return render_template('upload.html',
                                   error='Please upload a .txt file')

    return render_template('upload.html')


@app.route('/stats')
def stats():
    """Страница статистики"""
    total_docs = search_service.data_service.get_document_count()
    avg_doc_length = search_service.data_service.get_avg_doc_length()

    return render_template('stats.html',
                           total_docs=total_docs,
                           avg_doc_length=avg_doc_length)


@app.route('/file/<int:doc_id>')
def serve_file(doc_id):
    """Эндпоинт для отдачи файла"""
    if not search_service:
        abort(503, description="Service unavailable")

    doc = search_service.data_service.get_document_by_id(doc_id)
    if not doc:
        abort(404, description="Document not found")

    file_path = doc['file_path']

    if not os.path.exists(file_path):
        abort(404, description="File not found on disk")

    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        logging.error(f"Error serving file {file_path}: {e}")
        abort(500, description="Error serving file")


@app.route('/preview/<int:doc_id>')
def preview_file(doc_id):
    """Эндпоинт для предпросмотра содержимого файла"""
    if not search_service:
        abort(503, description="Service unavailable")

    doc = search_service.data_service.get_document_by_id(doc_id)
    if not doc:
        abort(404, description="Document not found")

    return render_template('preview.html',
                           doc=doc,
                           content=doc['content'])


def init_directories():
    """Инициализация необходимых директорий"""
    try:
        if not os.path.exists(WATCH_DIRECTORY):
            os.makedirs(WATCH_DIRECTORY, exist_ok=True)
            logging.info(f"Создана директория: {WATCH_DIRECTORY}")

        # Test write permissions
        test_file = os.path.join(WATCH_DIRECTORY, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logging.info(f"Directory {WATCH_DIRECTORY} is writable")

    except Exception as e:
        logging.error(f"Directory error: {e}")
        raise


def init_services():
    """Инициализация сервисов"""
    global search_service, file_watcher

    try:
        search_service = SearchService(DB_CONFIG)
        file_watcher = FileWatcher(WATCH_DIRECTORY, search_service, debounce_seconds=2.0)

        file_watcher.scan_existing_files()

        file_watcher.start()
        logging.info("Сервисы успешно инициализированы")

    except Exception as e:
        logging.error(f"Ошибка инициализации сервисов: {e}")
        raise


if __name__ == '__main__':
    init_directories()
    init_services()

    port = int(os.getenv('PORT', '5001'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'

    try:
        # use_reloader=False: иначе FileWatcher поднимается дважды
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    except KeyboardInterrupt:
        if file_watcher:
            file_watcher.stop()
    except Exception as e:
        logging.error(f"Ошибка запуска приложения: {e}")