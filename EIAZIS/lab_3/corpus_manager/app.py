import json
import os
import re
import tempfile
import traceback
from datetime import datetime
from io import BytesIO
from pathlib import Path

import nltk
from bs4 import BeautifulSoup
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for
from nltk import pos_tag
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize
from sqlalchemy import or_, text

from config import Config
from corpus_service import (
    analyze_sentence_syntax,
    build_document_syntax_analyses,
    export_syntax_report,
    filter_by_pos,
    get_concordance,
    get_corpus_stats,
    get_document,
    get_document_syntax_data,
    get_documents_list,
    get_lemma_stats,
    get_syntax_analysis,
    get_word_stats,
    search_words,
    update_syntax_analysis,
)
from models import Document, Sentence, Token, db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

ALLOWED_EXTENSIONS = {'html', 'htm'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

lemmatizer = WordNetLemmatizer()

NLTK_RESOURCES = {
    'punkt': 'tokenizers/punkt',
    'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger',
    'averaged_perceptron_tagger_eng': 'taggers/averaged_perceptron_tagger_eng',
    'wordnet': 'corpora/wordnet',
    'omw-1.4': 'corpora/omw-1.4',
}

for resource, lookup_path in NLTK_RESOURCES.items():
    try:
        nltk.data.find(lookup_path)
    except LookupError:
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            pass


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_text(text_value):
    if not text_value:
        return ''
    text_value = re.sub(r'\s+', ' ', text_value)
    return text_value.strip()


def _normalize_fragment(fragment):
    fragment = clean_text(fragment)
    fragment = fragment.replace(' ,', ',').replace(' .', '.').replace(' :', ':')
    return fragment.strip()


def _is_noise_fragment(fragment):
    lowered = fragment.lower()
    noise_markers = (
        'skip to main content',
        'main menu',
        'navigation',
        'privacy policy',
        'cookie',
        'accept all',
        'subscribe',
        'sign in',
        'log in',
        'create account',
        'donate',
        'table of contents',
        'jump to content',
        'edit links',
        'view history',
        'related changes',
        'special pages',
        'permanent link',
        'page information',
        'print/export',
        'get shortened url',
        'site map',
    )

    if len(fragment) < 25:
        return True
    if lowered in {'search', 'menu', 'home', 'about', 'contact'}:
        return True
    if any(marker in lowered for marker in noise_markers):
        return True

    alpha_chars = sum(char.isalpha() for char in fragment)
    if alpha_chars < 12:
        return True

    words = fragment.split()
    if len(words) < 5:
        return True

    unique_ratio = len(set(word.lower() for word in words)) / max(len(words), 1)
    if len(words) > 12 and unique_ratio < 0.45:
        return True

    uppercase_words = sum(word.isupper() for word in words if len(word) > 2)
    if uppercase_words > max(5, len(words) // 2):
        return True

    return False


def _extract_candidate_fragments(root):
    fragments = []

    for tag in root.find_all(('p', 'blockquote', 'pre')):
        text = _normalize_fragment(tag.get_text(' ', strip=True))
        if not text or _is_noise_fragment(text):
            continue
        fragments.append(text)

    if len(fragments) < 3:
        for tag in root.find_all('li'):
            text = _normalize_fragment(tag.get_text(' ', strip=True))
            if not text or _is_noise_fragment(text):
                continue
            if len(text) < 60 and not re.search(r'[.!?]$', text):
                continue
            fragments.append(text)

    if len(fragments) < 2:
        for tag in root.find_all(('article', 'section', 'main', 'div')):
            text = _normalize_fragment(tag.get_text(' ', strip=True))
            if not text or _is_noise_fragment(text):
                continue
            fragments.append(text)

    deduplicated = []
    seen = set()
    for fragment in fragments:
        key = fragment.lower()
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(fragment)

    filtered = []
    for fragment in deduplicated:
        lowered = fragment.lower()
        if any(
            lowered != other.lower() and lowered in other.lower() and len(other) > len(fragment) + 40
            for other in deduplicated
        ):
            continue
        filtered.append(fragment)

    return filtered


def _pick_content_root(soup):
    preferred_selectors = (
        'article',
        'main',
        '[role="main"]',
        '.content',
        '.post-content',
        '.entry-content',
        '.article-content',
        '.article-body',
        '#content',
        '#main-content',
        '.mw-parser-output',
    )

    best_root = None
    best_score = -1

    for selector in preferred_selectors:
        for candidate in soup.select(selector):
            score = len(candidate.get_text(' ', strip=True))
            if score > best_score:
                best_root = candidate
                best_score = score

    if best_root is not None and best_score >= 200:
        return best_root

    return soup.body or soup


def extract_text_from_html(file_storage):
    content = file_storage.read()
    decoded = content.decode('utf-8', errors='ignore')
    soup = BeautifulSoup(decoded, 'html.parser')

    for tag_name in ('script', 'style', 'noscript', 'svg', 'iframe', 'canvas', 'form'):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag_name in ('nav', 'header', 'footer', 'aside'):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(attrs={'aria-hidden': 'true'}):
        tag.decompose()

    for candidate in soup.find_all(True):
        attrs = getattr(candidate, 'attrs', None)
        if attrs is None:
            continue
        class_names = ' '.join(attrs.get('class', []))
        element_id = attrs.get('id', '')
        marker_tokens = set(re.findall(r'[a-z0-9_-]+', f"{class_names} {element_id}".lower()))
        if marker_tokens.intersection({
            'cookie', 'cookies', 'consent', 'banner', 'breadcrumb', 'breadcrumbs',
            'sidebar', 'menu', 'navbar', 'footer', 'header', 'pagination',
            'share', 'social', 'toolbar'
        }):
            candidate.decompose()

    content_root = _pick_content_root(soup)
    fragments = _extract_candidate_fragments(content_root)

    if not fragments:
        paragraph_fragments = []
        for tag in content_root.find_all('p'):
            text = _normalize_fragment(tag.get_text(' ', strip=True))
            if len(text) >= 40 and sum(char.isalpha() for char in text) >= 20:
                paragraph_fragments.append(text)
        fragments = paragraph_fragments

    if not fragments:
        fragments = [
            fragment for fragment in (_normalize_fragment(text) for text in content_root.stripped_strings)
            if fragment and not _is_noise_fragment(fragment)
        ]

    if not fragments:
        fragments = [
            fragment for fragment in (_normalize_fragment(text) for text in soup.stripped_strings)
            if fragment and not _is_noise_fragment(fragment)
        ]

    return clean_text(' '.join(fragments))


def split_sentences(text_value):
    try:
        sentences = sent_tokenize(text_value, language='english')
    except Exception:
        sentences = [part.strip() for part in re.split(r'(?<=[.!?])\s+', text_value) if part.strip()]
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 3]


def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    if treebank_tag.startswith('V'):
        return wordnet.VERB
    if treebank_tag.startswith('N'):
        return wordnet.NOUN
    if treebank_tag.startswith('R'):
        return wordnet.ADV
    return wordnet.NOUN


def extract_annotated_tokens(sentence_text):
    words = word_tokenize(sentence_text)
    tagged_words = pos_tag(words)
    annotated = []

    for position, (word, pos) in enumerate(tagged_words, start=1):
        if not re.search(r'[A-Za-z]', word):
            continue
        lemma = lemmatizer.lemmatize(word.lower(), get_wordnet_pos(pos))
        annotated.append({
            'word': word.lower(),
            'lemma': lemma,
            'pos': pos,
            'grammemes': pos,
            'position': position
        })

    return annotated


def process_file_direct(file_stream, filename, title, author, genre, year):
    extension = Path(filename).suffix.lower().replace('.', '')

    try:
        text_value = extract_text_from_html(file_stream)
        if not text_value or len(text_value) < 50:
            return None, 'HTML-файл слишком мал или не содержит извлекаемого текста'

        sentences = split_sentences(text_value)
        if not sentences:
            return None, 'Не удалось выделить предложения для анализа'

        document = Document(
            title=title,
            author=author,
            year=year,
            genre=genre,
            file_path=f'uploaded_{filename}',
            source_format=extension.upper(),
            text_content=text_value
        )
        db.session.add(document)
        db.session.flush()

        token_count = 0
        for sent_idx, sent_text in enumerate(sentences, start=1):
            sentence = Sentence(doc_id=document.id, text=sent_text, position=sent_idx)
            db.session.add(sentence)
            db.session.flush()

            for token_data in extract_annotated_tokens(sent_text):
                db.session.add(Token(sentence_id=sentence.id, **token_data))
                token_count += 1

        db.session.commit()
        analyses = build_document_syntax_analyses(document.id)
        return document, (
            f'Загружено {len(sentences)} предложений, {token_count} токенов, '
            f'{len(analyses)} синтаксических разборов'
        )
    except Exception as exc:
        db.session.rollback()
        print(f'Ошибка обработки файла:\n{traceback.format_exc()}')
        return None, str(exc)


@app.route('/')
def index():
    stats_data = get_corpus_stats()
    return render_template('index.html', stats=stats_data)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        search_type = request.form.get('search_type', 'word')
        results = search_words(query, search_type)
        return render_template('search.html', query=query, results=results, search_type=search_type)
    return render_template('search.html')


@app.route('/search_documents', methods=['GET', 'POST'])
def search_documents():
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        search_field = request.form.get('search_field', 'all')

        if not query:
            return redirect(url_for('documents'))

        results = search_in_documents(query, search_field)
        return render_template(
            'search_documents.html',
            query=query,
            results=results,
            search_field=search_field
        )

    return render_template('search_documents.html')


def search_in_documents(query, search_field='all'):
    query_pattern = f'%{query}%'

    if search_field == 'title':
        docs = Document.query.filter(Document.title.ilike(query_pattern)).all()
    elif search_field == 'author':
        docs = Document.query.filter(Document.author.ilike(query_pattern)).all()
    elif search_field == 'genre':
        docs = Document.query.filter(Document.genre.ilike(query_pattern)).all()
    elif search_field == 'text':
        sentences = Sentence.query.filter(Sentence.text.ilike(query_pattern)).limit(100).all()
        doc_ids = set(sentence.doc_id for sentence in sentences)
        docs = Document.query.filter(Document.id.in_(doc_ids)).all() if doc_ids else []

        for doc in docs:
            doc.matches = Sentence.query.filter(
                Sentence.doc_id == doc.id,
                Sentence.text.ilike(query_pattern)
            ).count()
    else:
        docs = Document.query.filter(
            or_(
                Document.title.ilike(query_pattern),
                Document.author.ilike(query_pattern),
                Document.genre.ilike(query_pattern),
                Document.text_content.ilike(query_pattern)
            )
        ).all()

    return docs


@app.route('/word/<word>')
def word_detail(word):
    stats = get_word_stats(word)
    return render_template('word_detail.html', stats=stats)


@app.route('/lemma/<lemma>')
def lemma_detail(lemma):
    stats = get_lemma_stats(lemma)
    return render_template('lemma_detail.html', stats=stats)


@app.route('/concordance')
def concordance():
    word = request.args.get('word', '')
    if word:
        lines = get_concordance(word)
        return render_template('concordance.html', word=word, lines=lines)
    return render_template('concordance.html')


@app.route('/stats')
def stats():
    return render_template('stats.html', stats=get_corpus_stats())


@app.route('/documents')
def documents():
    return render_template('documents.html', documents=get_documents_list())


@app.route('/document/<int:doc_id>')
def document(doc_id):
    return render_template('document.html', doc=get_document(doc_id))


@app.route('/syntax')
def syntax_documents():
    return render_template('syntax_documents.html', documents=get_documents_list())


@app.route('/document/<int:doc_id>/syntax')
def document_syntax(doc_id):
    doc, analyses = get_document_syntax_data(doc_id)
    return render_template('syntax_document.html', doc=doc, analyses=analyses)


@app.route('/syntax/<int:analysis_id>', methods=['GET', 'POST'])
def syntax_analysis_detail(analysis_id):
    analysis = get_syntax_analysis(analysis_id)
    if request.method == 'POST':
        analysis = update_syntax_analysis(
            analysis_id,
            request.form.get('edited_summary', ''),
            request.form.get('notes', '')
        )
        flash('Синтаксический разбор обновлён')
        return redirect(url_for('syntax_analysis_detail', analysis_id=analysis.id))

    payload = json.loads(analysis.payload_json) if analysis.payload_json else {}
    return render_template('syntax_sentence.html', analysis=analysis, payload=payload)


@app.route('/document/<int:doc_id>/syntax/rebuild', methods=['POST'])
def rebuild_syntax(doc_id):
    analyses = build_document_syntax_analyses(doc_id, force=True)
    flash(f'Синтаксический анализ перестроен. Обновлено разборов: {len(analyses)}')
    return redirect(url_for('document_syntax', doc_id=doc_id))


@app.route('/document/<int:doc_id>/syntax/export')
def export_syntax(doc_id):
    export_format = request.args.get('format', 'txt')
    report = export_syntax_report(doc_id)

    if export_format == 'json':
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as file_obj:
            json.dump(report, file_obj, ensure_ascii=False, indent=2)
            file_path = file_obj.name
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"syntax_report_{report['document']['id']}.json",
            mimetype='application/json'
        )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as file_obj:
        file_obj.write(f"Document: {report['document']['title']}\n")
        file_obj.write(f"Author: {report['document']['author'] or 'unknown'}\n")
        file_obj.write(f"Format: {report['document']['source_format'] or 'unknown'}\n")
        file_obj.write('=' * 80 + '\n\n')
        for item in report['analyses']:
            file_obj.write(f"Sentence {item['sentence_position']}: {item['sentence_text']}\n")
            file_obj.write(f"Summary: {item['summary']}\n")
            if item['notes']:
                file_obj.write(f"Notes: {item['notes']}\n")
            file_obj.write('Structure:\n')
            file_obj.write(f"{item['tree_view']}\n")
            file_obj.write('-' * 80 + '\n')
        file_path = file_obj.name

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"syntax_report_{report['document']['id']}.txt",
        mimetype='text/plain'
    )


@app.route('/api/syntax/<int:analysis_id>')
def api_syntax_analysis(analysis_id):
    analysis = get_syntax_analysis(analysis_id)
    payload = json.loads(analysis.payload_json) if analysis.payload_json else {}
    dep = payload.get('dependency_parse') or {}
    return jsonify({
        'analysis_id': analysis.id,
        'sentence_id': analysis.sentence_id,
        'sentence_text': analysis.sentence.text,
        'summary': analysis.edited_summary or analysis.summary,
        'parse_ms': dep.get('parse_ms'),
        'engine': dep.get('engine'),
        'payload': payload,
    })


@app.route('/api/syntax/analyze', methods=['POST'])
def api_syntax_analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text is required'}), 400
    result = analyze_sentence_syntax(text)
    payload = json.loads(result['payload_json'])
    dep = payload.get('dependency_parse') or {}
    return jsonify({
        'summary': result['summary'],
        'tree_view': result['tree_view'],
        'parse_ms': dep.get('parse_ms'),
        'engine': dep.get('engine'),
        'payload': payload,
    })


@app.route('/export/<int:doc_id>')
def export_document(doc_id):
    doc = get_document(doc_id)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as file_obj:
        file_obj.write(f'Title: {doc.title}\n')
        file_obj.write(f'Author: {doc.author}\n')
        file_obj.write(f'Genre: {doc.genre}\n')
        file_obj.write(f'Year: {doc.year}\n')
        file_obj.write('=' * 50 + '\n\n')
        for sent in doc.sentences.order_by('position'):
            file_obj.write(sent.text + '\n')
    return send_file(
        file_obj.name,
        as_attachment=True,
        download_name=f'{doc.title}.txt',
        mimetype='text/plain'
    )


@app.route('/upload', methods=['GET', 'POST'])
def upload_document():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Ошибка: не выбран файл')
            return redirect(request.url)

        file_storage = request.files['file']
        if file_storage.filename == '':
            flash('Ошибка: имя файла пустое')
            return redirect(request.url)

        if not allowed_file(file_storage.filename):
            flash('Для варианта 6 поддерживаются только HTML-файлы')
            return redirect(request.url)

        title = request.form.get('title', '').strip() or file_storage.filename
        author = request.form.get('author', '').strip() or 'Unknown'
        genre = request.form.get('genre', '').strip() or 'Scientific / analytical text'
        year = request.form.get('year', '').strip()
        year_int = None

        if year:
            try:
                year_int = int(year)
            except ValueError:
                flash('Предупреждение: год должен быть числом, поэтому значение пропущено')

        file_content = file_storage.read()
        if not file_content:
            flash('Ошибка: файл пустой')
            return redirect(request.url)

        document_obj, message = process_file_direct(
            BytesIO(file_content),
            file_storage.filename,
            title,
            author,
            genre,
            year_int
        )

        if document_obj:
            flash(f'Документ "{title}" загружен. {message}')
            return redirect(url_for('document', doc_id=document_obj.id))

        flash(f'Ошибка при обработке: {message}')
        return redirect(request.url)

    return render_template('upload.html')


@app.route('/delete_document/<int:doc_id>', methods=['POST'])
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)

    try:
        start_time = datetime.now()
        doc_title = doc.title
        db.session.execute(
            text(
                'DELETE FROM syntax_analyses '
                'WHERE sentence_id IN (SELECT id FROM sentences WHERE doc_id = :doc_id)'
            ),
            {'doc_id': doc_id}
        )
        db.session.execute(
            text('DELETE FROM tokens WHERE sentence_id IN (SELECT id FROM sentences WHERE doc_id = :doc_id)'),
            {'doc_id': doc_id}
        )
        db.session.execute(text('DELETE FROM sentences WHERE doc_id = :doc_id'), {'doc_id': doc_id})
        db.session.execute(text('DELETE FROM documents WHERE id = :doc_id'), {'doc_id': doc_id})
        db.session.commit()

        duration = (datetime.now() - start_time).total_seconds()
        flash(f'Документ "{doc_title}" удалён за {duration:.2f} секунд')
    except Exception as exc:
        db.session.rollback()
        flash(f'Ошибка при удалении: {exc}')

    return redirect(url_for('documents'))


@app.route('/delete_all_documents', methods=['POST'])
def delete_all_documents():
    try:
        start_time = datetime.now()
        db.session.execute(text('DELETE FROM syntax_analyses'))
        db.session.execute(text('DELETE FROM tokens'))
        db.session.execute(text('DELETE FROM sentences'))
        db.session.execute(text('DELETE FROM documents'))
        db.session.commit()
        duration = (datetime.now() - start_time).total_seconds()
        flash(f'Все документы и синтаксические разборы удалены за {duration:.2f} секунд')
    except Exception as exc:
        db.session.rollback()
        flash(f'Ошибка: {exc}')

    return redirect(url_for('documents'))


@app.route('/filter')
def filter_page():
    return render_template('filter.html')


@app.route('/api/filter', methods=['POST'])
def api_filter():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Нет данных'}), 400

        pos = data.get('pos', '')
        if not pos:
            return jsonify({'success': False, 'error': 'Не указана часть речи'}), 400

        results = filter_by_pos(pos)
        return jsonify({'success': True, 'pos': pos, 'total': len(results), 'results': results})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/help')
def help_page():
    return render_template('help.html')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
