# file_processor.py
import os
import re
from langdetect import detect, DetectorFactory
import chardet

DetectorFactory.seed = 0


def read_file(file_path):
    """
    Читает файл и возвращает информацию о его содержимом
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.txt':
        text = read_txt(file_path)
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")

    language = detect_language(text)
    cleaned_text = clean_text(text, language)

    return {
        'text': cleaned_text,
        'language': language,
        'file_type': file_extension
    }


def read_txt(file_path):
    """
    Читает текстовый файл с автоматическим определением кодировки
    """
    try:
        # Определяем кодировку
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            encoding = chardet.detect(raw_data)['encoding']

            if encoding is None:
                encoding = 'utf-8'

        # Читаем файл в правильной кодировке
        with open(file_path, 'r', encoding=encoding, errors='replace') as file:
            return file.read()

    except Exception as e:
        raise ValueError(f"Ошибка чтения файла: {str(e)}")


def detect_language(text):
    """
    Определяет язык текста
    """
    try:
        # Берем достаточно большой кусок текста для точного определения
        sample_text = text[:1000] if len(text) > 1000 else text
        if len(sample_text.strip()) < 10:
            return 'ru'  # По умолчанию русский

        lang = detect(sample_text)
        return 'ru' if lang == 'ru' else 'en'
    except:
        return 'ru'  # По умолчанию русский при ошибке


def clean_text(text, language):
    """
    Очищает текст от лишних пробелов и форматирования
    """

    text = re.sub(r'\s+', ' ', text)

    if language == 'ru':
        text = re.sub(r'[^\w\sа-яА-ЯёЁ\-.,!?;:()]', '', text)
    else:
        text = re.sub(r'[^\w\s\-.,!?;:()]', '', text)

    return text.strip()


def split_into_sentences(text, language):
    """
    Разбивает текст на предложения
    """
    if language == 'ru':
        sentences = re.split(r'(?<=[.!?])\s+', text)
    else:
        sentences = re.split(r'(?<=[.!?])\s+', text)

    return [s.strip() for s in sentences if s.strip()]


def split_into_paragraphs(text):
    """
    Разбивает текст на абзацы
    """
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]