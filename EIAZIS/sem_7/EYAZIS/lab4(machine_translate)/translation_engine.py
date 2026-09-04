import os
import ollama
import time
import sqlite3
import re
from datetime import datetime
from typing import Optional, Dict, List
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import spacy
import base64
import subprocess
import sys

try:
    import imgkit

    HAS_IMGKIT = True
except ImportError:
    HAS_IMGKIT = False

nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)


class AdvancedTranslator:
    def __init__(self, model_name: str = "zongwei/gemma3-translator:4b", use_cache: bool = True):
        self.model_name = model_name
        self.use_cache = use_cache

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        if self.use_cache:
            self._init_cache()

    def _init_cache(self):
        self.conn = sqlite3.connect('translation_cache.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_text TEXT UNIQUE,
                german_text TEXT,
                word_count INT,
                translation_word_count INT,
                model_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def _get_cached_translation(self, english_text: str) -> Optional[dict]:
        if not self.use_cache:
            return None

        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT german_text, word_count, translation_word_count FROM translations WHERE english_text = ? AND model_name = ?',
            (english_text, self.model_name)
        )
        result = cursor.fetchone()
        if result:
            return {
                'german_text': result[0],
                'word_count': result[1],
                'translation_word_count': result[2]
            }
        return None

    def _cache_translation(self, english_text: str, german_text: str, word_count: int, translation_word_count: int):
        if not self.use_cache:
            return

        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO translations 
               (english_text, german_text, word_count, translation_word_count, model_name) VALUES (?, ?, ?, ?, ?)''',
            (english_text, german_text, word_count, translation_word_count, self.model_name)
        )
        self.conn.commit()

    def count_words(self, text: str) -> int:
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    def get_grammatical_info(self, text: str, language: str = 'english') -> List[Dict]:
        words = word_tokenize(text)
        pos_tags = pos_tag(words)

        grammatical_info = []
        for word, pos in pos_tags:
            if word.isalpha():
                info = {
                    'word': word,
                    'pos': self._get_pos_description(pos, language),
                    'tag': pos
                }
                grammatical_info.append(info)

        return grammatical_info

    def _get_pos_description(self, pos_tag: str, language: str) -> str:
        pos_descriptions = {
            'NN': 'Noun', 'NNS': 'Noun plural', 'NNP': 'Proper noun',
            'VB': 'Verb', 'VBD': 'Verb past tense', 'VBG': 'Verb gerund',
            'VBN': 'Verb past participle', 'VBP': 'Verb present',
            'VBZ': 'Verb 3rd person singular',
            'JJ': 'Adjective', 'JJR': 'Adjective comparative', 'JJS': 'Adjective superlative',
            'RB': 'Adverb', 'RBR': 'Adverb comparative', 'RBS': 'Adverb superlative',
            'PRP': 'Personal pronoun', 'PRP$': 'Possessive pronoun',
            'DT': 'Determiner', 'IN': 'Preposition', 'CC': 'Conjunction',
            'CD': 'Cardinal number', 'EX': 'Existential there',
            'FW': 'Foreign word', 'LS': 'List marker', 'MD': 'Modal',
            'PDT': 'Predeterminer', 'POS': 'Possessive ending',
            'RP': 'Particle', 'SYM': 'Symbol', 'TO': 'to',
            'UH': 'Interjection', 'WDT': 'Wh-determiner', 'WP': 'Wh-pronoun',
            'WP$': 'Possessive wh-pronoun', 'WRB': 'Wh-adverb'
        }
        return pos_descriptions.get(pos_tag, pos_tag)

    def get_frequency_list(self, text: str, grammatical_info: List[Dict]) -> List[Dict]:
        words = [word for word in re.findall(r'\b\w+\b', text.lower())]
        word_freq = Counter(words)
        grammar_dict = {info['word'].lower(): info for info in grammatical_info}

        frequency_list = []
        for word, count in word_freq.most_common():
            grammar = grammar_dict.get(word, {'pos': 'Unknown', 'tag': 'UNK'})
            frequency_list.append({
                'word': word,
                'count': count,
                'pos': grammar['pos'],
                'tag': grammar['tag']
            })

        return frequency_list

    def _generate_syntax_tree_with_spacy(self, sentence: str) -> str:
        try:
            from spacy import displacy

            sentence_text_stripped = sentence.strip()
            doc = self.nlp(sentence_text_stripped)

            html = displacy.render(doc, style='dep', jupyter=False, options={
                'compact': False,
                'color': '#000000',
                'bg': '#ffffff',
                'font': 'Arial',
                'distance': 120,
                'arrow_spacing': 0.5
            })

            image_data = self._html_to_image(html, sentence)
            if image_data:
                return image_data

            return self._wrap_html_for_display(html, sentence)

        except Exception as e:
            return self._create_text_fallback(sentence)

    def _html_to_image(self, html: str, sentence: str) -> Optional[str]:
        if HAS_IMGKIT:
            try:
                wkhtmltoimage_paths = [
                    'C:\\programmes\\wkhtmltopdf\\bin\\wkhtmltoimage.exe',
                    'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe',
                    '/usr/local/bin/wkhtmltoimage',
                    '/usr/bin/wkhtmltoimage',
                    'wkhtmltoimage'
                ]

                config = None
                for path in wkhtmltoimage_paths:
                    if os.path.exists(path):
                        config = imgkit.config(wkhtmltoimage=path)
                        break

                if config is None:
                    config = imgkit.config()

                options = {
                    'format': 'png',
                    'width': 1200,
                    'quality': 100,
                    'enable-local-file-access': None,
                    'disable-smart-width': None,
                    'log-level': 'none'
                }

                styled_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        .syntax-tree-body {{ 
                            margin: 20px; 
                            background: white;
                            font-family: Arial, sans-serif;
                        }}
                        .displacy-container {{
                            max-width: 100%;
                            overflow: visible;
                        }}
                        .syntax-tree-title {{
                            color: #333;
                            margin-bottom: 20px;
                            font-size: 18px;
                        }}
                    </style>
                </head>
                <body class="syntax-tree-body">
                    <h3 class="syntax-tree-title">Syntax Tree: "{sentence}"</h3>
                    {html}
                </body>
                </html>
                """

                img_data = imgkit.from_string(styled_html, False, options=options, config=config)
                image_base64 = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/png;base64,{image_base64}"

            except Exception:
                pass
        return None

    def _wrap_html_for_display(self, html: str, sentence: str) -> str:
        wrapped_html = f"""
        <div class="syntax-tree-wrapper">
            <h4 class="syntax-tree-title">Syntax Tree: "{sentence}"</h4>
            <div class="syntax-tree-content">
                {html}
            </div>
        </div>
        """
        return wrapped_html

    def _create_text_fallback(self, sentence: str) -> str:
        try:
            doc = self.nlp(sentence.strip())
            text_tree = []

            for token in doc:
                text_tree.append(
                    f"{token.text:15} | {token.pos_:10} | {token.dep_:15} | {token.head.text}"
                )

            tree_text = "\n".join(text_tree)
            return f"""
            <div class="text-fallback-wrapper">
                <h4 class="text-fallback-title">Dependency Analysis: "{sentence}"</h4>
                <pre class="text-fallback-content">
Token            | POS        | Dependency     | Head
{'-' * 60}
{tree_text}
                </pre>
            </div>
            """
        except Exception as e:
            return f"<div class='error-message'>Error creating syntax tree: {str(e)}</div>"

    def get_syntax_tree(self, sentence: str) -> str:
        try:
            sentence = sentence.strip()
            if not sentence:
                return "Please provide a valid sentence."

            return self._generate_syntax_tree_with_spacy(sentence)

        except Exception as e:
            error_msg = f"Error generating syntax tree: {str(e)}"
            return f"<div class='error-message'>{error_msg}</div>"

    def translate_with_stats(self, text: str) -> dict:
        start_time = time.time()
        cached_result = self._get_cached_translation(text)

        if cached_result:
            end_time = time.time()
            return {
                'original': text,
                'translation': cached_result['german_text'],
                'time_taken': end_time - start_time,
                'cached': True,
                'model': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'word_count': cached_result['word_count'],
                'translation_word_count': cached_result['translation_word_count']
            }

        prompt = f"Translate from English to German: {text}"

        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={'temperature': 0.1}
            )

            translation = response['response'].strip()
            end_time = time.time()
            translation = self._clean_translation(translation)
            word_count = self.count_words(text)
            translation_word_count = self.count_words(translation)

            self._cache_translation(text, translation, word_count, translation_word_count)

            return {
                'original': text,
                'translation': translation,
                'time_taken': end_time - start_time,
                'cached': False,
                'model': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'word_count': word_count,
                'translation_word_count': translation_word_count
            }

        except Exception as e:
            return {
                'original': text,
                'translation': f"Error: {e}",
                'time_taken': 0,
                'cached': False,
                'model': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'error': True,
                'word_count': 0,
                'translation_word_count': 0
            }

    def _clean_translation(self, text: str) -> str:
        for prefix in ['German:', 'Translation:', '»', '«', 'Here\'s the German translation:']:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()

        return text

    def save_to_file(self, translation_data: dict, filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"translation_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== ENGLISH TO GERMAN TRANSLATION RESULTS ===\n\n")
            f.write(f"Translation Date: {translation_data['timestamp']}\n")
            f.write(f"Model: {translation_data['model']}\n")
            f.write(f"Translation Time: {translation_data['time_taken']:.2f}s\n")
            f.write(f"From Cache: {translation_data.get('cached', False)}\n\n")

            f.write("ORIGINAL TEXT:\n")
            f.write("-" * 50 + "\n")
            f.write(translation_data['original'] + "\n\n")

            f.write(f"Word Count: {translation_data.get('word_count', 0)}\n\n")

            f.write("TRANSLATED TEXT:\n")
            f.write("-" * 50 + "\n")
            f.write(translation_data['translation'] + "\n\n")

            f.write(f"Translated Word Count: {translation_data.get('translation_word_count', 0)}\n\n")

            if 'grammatical_info' in translation_data:
                f.write("GRAMMATICAL INFORMATION (English):\n")
                f.write("-" * 50 + "\n")
                for info in translation_data['grammatical_info']:
                    f.write(f"{info['word']:15} - {info['pos']} ({info['tag']})\n")
                f.write("\n")

            if 'frequency_list' in translation_data:
                f.write("WORD FREQUENCY LIST (English):\n")
                f.write("-" * 50 + "\n")
                for item in translation_data['frequency_list']:
                    f.write(f"{item['word']:15} - Count: {item['count']:2} - {item['pos']}\n")
                f.write("\n")

            if 'syntax_tree' in translation_data:
                f.write("SYNTAX TREE:\n")
                f.write("-" * 50 + "\n")
                f.write(translation_data['syntax_tree'] + "\n")

        return filename