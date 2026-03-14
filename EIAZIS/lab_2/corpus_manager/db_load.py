#!/usr/bin/env python3
"""
Скрипт для загрузки и разметки текстов в корпус.
Поддерживает форматы: .txt, .docx, .pdf
Использует pymorphy2 для морфологического анализа.
"""

import os
import sys
import re
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import pymorphy2
from docx import Document as DocxDocument
import PyPDF2
from sqlalchemy import text

# Добавляем путь к проекту
sys.path.append(os.path.dirname(__file__))

from app import app, db
from models import Document, Sentence, Token

# Скачиваем необходимые данные nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Инициализируем морфологический анализатор
morph = pymorphy2.MorphAnalyzer()

def extract_text_from_txt(filepath):
    """Извлекает текст из TXT файла с перебором кодировок"""
    encodings = ['utf-8', 'cp1251', 'koi8-r', 'latin1', 'cp866']
    
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Если ничего не помогло, читаем в бинарном режиме и игнорируем ошибки
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_text_from_docx(filepath):
    """Извлекает текст из DOCX файла"""
    try:
        doc = DocxDocument(filepath)
        return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        print(f"  ⚠️ Ошибка чтения DOCX: {e}")
        return ""

def extract_text_from_pdf(filepath):
    """Извлекает текст из PDF файла"""
    text = ''
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
    except Exception as e:
        print(f"  ⚠️ Ошибка чтения PDF: {e}")
    return text

def clean_text(text):
    """Очищает текст от лишних символов"""
    if not text:
        return ""
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем спецсимволы, но оставляем буквы, цифры и знаки препинания
    text = re.sub(r'[^\w\s.,!?;:()\-"«»]', '', text)
    return text.strip()

def process_file(filepath, title=None, author='Неизвестен', year=None, genre='Литературоведение'):
    """
    Основная функция: разметка и сохранение файла в базу
    """
    if not title:
        title = Path(filepath).stem
    
    print(f"\n📄 Обработка: {title}")
    
    # Извлекаем текст в зависимости от формата
    ext = Path(filepath).suffix.lower()
    try:
        if ext == '.txt':
            text = extract_text_from_txt(filepath)
        elif ext == '.docx':
            text = extract_text_from_docx(filepath)
        elif ext == '.pdf':
            text = extract_text_from_pdf(filepath)
        else:
            print(f"  ⚠️ Неподдерживаемый формат: {ext}")
            return None
        
        if not text or len(text.strip()) < 100:
            print(f"  ⚠️ Файл слишком мал или пуст")
            return None
        
        # Очищаем текст
        text = clean_text(text)
        
    except Exception as e:
        print(f"  ❌ Ошибка чтения файла: {e}")
        return None
    
    # Создаём документ в базе
    doc = Document(
        title=title,
        author=author,
        year=year,
        genre=genre,
        file_path=str(filepath)
    )
    db.session.add(doc)
    db.session.commit()
    print(f"  📝 Документ создан, ID: {doc.id}")
    
    # Токенизация на предложения
    try:
        sentences = sent_tokenize(text, language='russian')
    except:
        # Fallback: простая токенизация по знакам препинания
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    sent_count = 0
    token_count = 0
    
    for sent_idx, sent_text in enumerate(sentences, start=1):
        if len(sent_text.strip()) < 10:  # Пропускаем слишком короткие предложения
            continue
            
        sent = Sentence(doc_id=doc.id, text=sent_text.strip(), position=sent_idx)
        db.session.add(sent)
        db.session.flush()
        sent_count += 1
        
        # Токенизация на слова
        try:
            words = word_tokenize(sent_text, language='russian')
        except:
            # Простая токенизация по пробелам
            words = sent_text.split()
        
        # Фильтруем слова (оставляем только слова с буквами)
        words = [w for w in words if re.search(r'[а-яА-ЯёЁ]', w)]
        
        for pos_in_sent, word in enumerate(words, start=1):
            try:
                parsed = morph.parse(word)[0]
                lemma = parsed.normal_form
                pos = parsed.tag.POS or 'UNKN'
                gram = str(parsed.tag)
                
                token = Token(
                    sentence_id=sent.id,
                    word=word.lower(),
                    lemma=lemma,
                    pos=pos,
                    grammemes=gram,
                    position=pos_in_sent
                )
                db.session.add(token)
                token_count += 1
                
                # Коммитим каждые 1000 токенов для экономии памяти
                if token_count % 1000 == 0:
                    db.session.commit()
                    print(f"    ...обработано {token_count} токенов")
                    
            except Exception as e:
                print(f"     Ошибка обработки слова '{word}': {e}")
                continue
    
    db.session.commit()
    print(f"  Загружено: {sent_count} предложений, {token_count} токенов")
    return doc

def load_all_files(folder='uploads'):
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f" Папка {folder} не найдена. Создаю...")
        folder_path.mkdir(exist_ok=True)
        print(f" Папка создана. Положите в неё текстовые файлы и запустите скрипт снова.")
        return
    
    files = list(folder_path.glob('*'))
    supported = [f for f in files if f.suffix.lower() in ['.txt', '.docx', '.pdf']]
    
    if not supported:
        print(f" В папке {folder} нет поддерживаемых файлов (.txt, .docx, .pdf)")
        print("Добавьте файлы в папку uploads/ и запустите скрипт снова.")
        return
    
    print(f" Найдено файлов для загрузки: {len(supported)}")
    
    stats = {'success': 0, 'failed': 0}
    
    for file_path in supported:
        try:
            print(f"\n{'='*60}")
            result = process_file(str(file_path))
            if result:
                stats['success'] += 1
            else:
                stats['failed'] += 1
        except Exception as e:
            print(f" Критическая ошибка при обработке {file_path.name}: {e}")
            stats['failed'] += 1
    
if __name__ == '__main__':
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            print(" Подключение к базе данных успешно")
        except Exception as e:
            print(f" Ошибка подключения к БД: {e}")
            sys.exit(1)
        
        load_all_files()