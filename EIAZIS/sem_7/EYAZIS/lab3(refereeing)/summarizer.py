import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pymorphy3
import requests
import json
import time

# Скачиваем необходимые данные nltk при первом запуске
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextSummarizer:
    def __init__(self):
        try:
            self.russian_stopwords = set(stopwords.words('russian'))
            self.english_stopwords = set(stopwords.words('english'))
        except:
            self.russian_stopwords = set()
            self.english_stopwords = set()

        self.english_lemmatizer = WordNetLemmatizer()
        self.russian_analyzer = pymorphy3.MorphAnalyzer()

        # Настройки для Ollama API
        self.ollama_base_url = "http://localhost:11434"
        self.semantic_model = "llama3.2"

    def generate_semantic_keywords_with_ollama(self, text, language, num_keywords=10):
        """
        Создает семантические ключевые слова с использованием Ollama
        """
        try:
            # Подготавливаем промпт в зависимости от языка
            if language == 'ru':
                system_prompt = """Ты - эксперт по анализу текстов. Извлеки самые важные ключевые слова и фразы из текста.
    Верни ТОЛЬКО список ключевых слов и фраз, разделенных запятыми, без номеров, без дополнительного текста.
    Ключевые слова должны отражать основные темы, концепции и суть текста."""

                user_prompt = f"""Извлеки {num_keywords} самых важных ключевых слов и фраз из следующего текста.
    Верни только список, разделенный запятыми:

    {text}

    Ключевые слова:"""
            else:
                system_prompt = """You are a text analysis expert. Extract the most important keywords and phrases from the text.
    Return ONLY a list of keywords and phrases separated by commas, without numbers, without additional text.
    Keywords should reflect the main topics, concepts and essence of the text."""

                user_prompt = f"""Extract the top {num_keywords} most important keywords and phrases from the following text.
    Return only a comma-separated list:

    {text}

    Keywords:"""

            # Формируем запрос к Ollama API
            payload = {
                "model": self.semantic_model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Низкая температура для более предсказуемых результатов
                    "top_p": 0.8,
                    "num_predict": 300
                }
            }

            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                keywords_text = result.get('response', '').strip()

                # Очищаем ответ и преобразуем в список
                keywords_text = re.sub(r'^(Ключевые слова:|Keywords:)\s*', '', keywords_text, flags=re.IGNORECASE)
                keywords_text = re.sub(r'[\[\]\d\.]', '', keywords_text)  # Убираем номера и скобки

                # Разделяем по запятым и очищаем
                keywords_list = [kw.strip() for kw in keywords_text.split(',')]
                keywords_list = [kw for kw in keywords_list if kw and len(kw) > 1]  # Убираем пустые и слишком короткие

                # Ограничиваем количество и возвращаем
                return keywords_list[:num_keywords]
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            raise Exception("Превышено время ожидания ответа от Ollama при генерации ключевых слов.")
        except requests.exceptions.ConnectionError:
            raise Exception("Не удалось подключиться к Ollama. Убедитесь, что Ollama запущен на localhost:11434.")
        except Exception as e:
            raise Exception(f"Ошибка при создании семантических ключевых слов: {str(e)}")

    def preprocess_text(self, text, language):
        """
        Предобработка текста: токенизация, удаление стоп-слов, лемматизация
        """
        # Токенизация слов
        words = re.findall(r'\b\w+\b', text.lower())

        if language == 'ru':
            filtered_words = [
                word for word in words
                if word not in self.russian_stopwords and len(word) > 2
            ]
            processed_words = [
                self.russian_analyzer.parse(word)[0].normal_form
                for word in filtered_words
            ]
        else:
            # Обработка для английского языка
            filtered_words = [
                word for word in words
                if word not in self.english_stopwords and len(word) > 2
            ]
            # Лемматизация для английского
            processed_words = [
                self.english_lemmatizer.lemmatize(word)
                for word in filtered_words
            ]

        return {
            'processed_words': processed_words,
            'original_words': words
        }

    def calculate_term_weights(self, processed_text):
        """
        Вычисляет веса терминов на основе частоты встречаемости
        """
        word_freq = Counter(processed_text['processed_words'])
        total_words = len(processed_text['processed_words'])

        term_weights = {
            word: freq / total_words
            for word, freq in word_freq.items()
        }

        return term_weights

    def split_into_sentences(self, text, language):
        """
        Разбивает текст на предложения
        """
        # Простое разбиение по точкам, восклицательным и вопросительным знакам
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def calculate_sentence_scores(self, sentences, term_weights, text_length):
        """
        Вычисляет оценку важности для каждого предложения
        """
        sentence_scores = []

        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence.lower())
            score = 0
            significant_terms = 0

            for word in words:
                if word in term_weights:
                    score += term_weights[word]
                    significant_terms += 1

            if significant_terms > 0:
                score /= significant_terms

            position_bonus = 1.0 + (0.5 * (1 - i / len(sentences)))
            score *= position_bonus

            sentence_scores.append((sentence, score))

        return sentence_scores

    def generate_classic_summary(self, sentences_with_scores, num_sentences=5):
        """
        Генерирует классический реферат из наиболее важных предложений
        """
        if not sentences_with_scores:
            return ""

        sorted_sentences = sorted(
            sentences_with_scores,
            key=lambda x: x[1],
            reverse=True
        )[:num_sentences]

        original_sentences = [s[0] for s in sentences_with_scores]
        selected_sentences = [s[0] for s in sorted_sentences]

        summary_sentences = []
        for sent in original_sentences:
            if sent in selected_sentences:
                summary_sentences.append(sent)

        return ' '.join(summary_sentences)

    def generate_keyword_summary(self, term_weights, num_keywords=10):
        """
        Генерирует список ключевых слов
        """
        sorted_keywords = sorted(
            term_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )[:num_keywords]

        return [keyword for keyword, weight in sorted_keywords]

    def create_semantic_summary_with_ollama(self, text, language):
        """
        Создает семантический реферат с использованием Ollama
        """
        try:
            # Подготавливаем промпт в зависимости от языка
            if language == 'ru':
                system_prompt = """Ты - эксперт по анализу и реферированию текстов. Создай качественный реферат, который:
1. Точно передает основные идеи и ключевые моменты
2. Сохраняет смысловую целостность оригинала
3. Выделяет важные детали и выводы
4. Начинай ответ сразу с реферата

Реферат должен быть в 3-4 раза короче оригинала и содержать только самую важную информацию."""

                user_prompt = f"""Проанализируй следующий текст и создай качественный реферат на русском языке:

{text}

Реферат:"""
            else:
                system_prompt = """You are an expert in text analysis and summarization. Create a high-quality summary that:
1. Accurately conveys main ideas and key points
2. Preserves semantic integrity of the original
3. Highlights important details and conclusions
4. Start answer right from summary

The summary should be 3-4 times shorter than the original and contain only the most important information."""

                user_prompt = f"""Analyze the following text and create a high-quality summary in English:

{text}

Summary:"""

            # Формируем запрос к Ollama API
            payload = {
                "model": self.semantic_model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 1500
                }
            }

            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120  # Увеличиваем таймаут для больших текстов
            )

            if response.status_code == 200:
                result = response.json()
                semantic_summary = result.get('response', '').strip()

                # Очищаем ответ от возможных артефактов
                semantic_summary = re.sub(r'^Реферат:\s*', '', semantic_summary)
                semantic_summary = re.sub(r'^Summary:\s*', '', semantic_summary)

                return semantic_summary
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            raise Exception("Превышено время ожидания ответа от Ollama. Попробуйте уменьшить размер текста.")
        except requests.exceptions.ConnectionError:
            raise Exception("Не удалось подключиться к Ollama. Убедитесь, что Ollama запущен на localhost:11434.")
        except Exception as e:
            raise Exception(f"Ошибка при создании семантического реферата: {str(e)}")

    def create_summary(self, text, language):
        """
        Основная функция генерации реферата с использованием всех методов
        """
        if not text or len(text.strip()) == 0:
            return {
                'classic_summary': "Текст слишком короткий для реферирования",
                'semantic_summary': "Текст слишком короткий для реферирования",
                'keyword_summary': [],
                'semantic_keywords': [],
                'language': language,
                'original_length': 0,
                'summary_length': 0,
                'semantic_summary_length': 0,
                'compression_ratio': 0,
                'semantic_compression_ratio': 0
            }

        # Генерируем классический реферат
        sentences = self.split_into_sentences(text, language)
        if len(sentences) == 0:
            return {
                'classic_summary': "Не удалось разбить текст на предложения",
                'semantic_summary': "Не удалось разбить текст на предложения",
                'keyword_summary': [],
                'semantic_keywords': [],
                'language': language,
                'original_length': len(text),
                'summary_length': 0,
                'semantic_summary_length': 0,
                'compression_ratio': 0,
                'semantic_compression_ratio': 0
            }

        processed_text = self.preprocess_text(text, language)
        term_weights = self.calculate_term_weights(processed_text)

        sentence_scores = self.calculate_sentence_scores(
            sentences, term_weights, len(text)
        )

        num_sentences = min(max(3, len(sentences) // 5), 10)
        classic_summary = self.generate_classic_summary(sentence_scores, num_sentences)
        keyword_summary = self.generate_keyword_summary(term_weights, num_keywords=10)

        # Генерируем семантические компоненты
        semantic_keywords = []
        semantic_summary = ""

        try:
            # Параллельно генерируем семантический реферат и ключевые слова
            # В реальном приложении можно использовать threading для параллельного выполнения
            semantic_summary = self.create_semantic_summary_with_ollama(text, language)
            semantic_keywords = self.generate_semantic_keywords_with_ollama(text, language)
        except Exception as e:
            error_msg = f"Ошибка семантического анализа: {str(e)}"
            semantic_summary = error_msg
            semantic_keywords = ["Не удалось извлечь ключевые слова"]

        # Рассчитываем метрики
        original_length = len(text)
        classic_summary_length = len(classic_summary)
        semantic_summary_length = len(semantic_summary) if semantic_summary else 0

        classic_compression_ratio = round((1 - classic_summary_length / original_length) * 100,
                                          2) if original_length > 0 else 0
        semantic_compression_ratio = round((1 - semantic_summary_length / original_length) * 100,
                                           2) if original_length > 0 and semantic_summary_length > 0 else 0

        return {
            'classic_summary': classic_summary,
            'semantic_summary': semantic_summary,
            'keyword_summary': keyword_summary,
            'semantic_keywords': semantic_keywords,
            'language': language,
            'original_length': original_length,
            'summary_length': classic_summary_length,
            'semantic_summary_length': semantic_summary_length,
            'compression_ratio': classic_compression_ratio,
            'semantic_compression_ratio': semantic_compression_ratio
        }