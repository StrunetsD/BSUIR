import nltk
import math
import logging
import ollama 
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from data_service import DataService
import os
import json

# Загрузка ресурсов NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db_config, k1=2.0, b=0.75):
        self.data_service = DataService(db_config)
        self.k1 = k1
        self.b = b
        self.stop_words = set(stopwords.words('english'))
        self.stemmer = PorterStemmer()

        ollama_host = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
        self.ollama_client = ollama.Client(host=ollama_host)
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')

    def preprocess_text(self, text):
        """Предобработка текста: токенизация, удаление стоп-слов, стемминг"""
        tokens = word_tokenize(text.lower())
        filtered_tokens = [
            self.stemmer.stem(token)
            for token in tokens
            if token.isalnum() and token not in self.stop_words
        ]
        return filtered_tokens

    def calculate_term_frequencies(self, tokens):
        """Подсчет частот терминов"""
        term_freq = {}
        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1
        return term_freq

    def calculate_idf(self, term):
        """Расчет IDF для термина с использованием стандартной формулы"""
        N = self.data_service.get_document_count()
        n_term = self.data_service.get_term_doc_count(term)

        if n_term == 0 or N == 0:
            return 0

        # Стандартная формула IDF, которая всегда положительна
        idf =  math.log((N) / (n_term))

        return idf

    def calculate_bm25_score(self, doc_terms, query_terms, doc_length, avg_doc_length):
        """Расчет BM25 score для документа"""
        score = 0.0
        avgdl = avg_doc_length if avg_doc_length > 0 else 1.0

        for term in query_terms:
            if term not in doc_terms:
                continue

            idf = self.calculate_idf(term)
            f = doc_terms[term]
            D = doc_length

            # Формула BM25
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * (D / avgdl))
            term_score = idf * (numerator / denominator)
            score += term_score

        return score

    def index_document(self, file_path, content, title=None):
        """Индексирование документа"""
        try:
            if title is None:
                title = os.path.basename(file_path)

            # Предобработка текста
            tokens = self.preprocess_text(content)
            doc_length = len(tokens)

            # Подсчет частот терминов
            term_frequencies = self.calculate_term_frequencies(tokens)

            # Сохранение документа
            last_modified = os.path.getmtime(file_path)
            doc_id = self.data_service.add_document(
                title, content, file_path, last_modified, doc_length
            )

            # Обновление статистики терминов
            self.data_service.update_term_stats(term_frequencies)
            self.data_service.add_document_terms(doc_id, term_frequencies)

            logger.info(f"Документ проиндексирован: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка индексирования {file_path}: {e}")
            return False

    def index_file(self, file_path):
        """Индексирование файла"""
        try:
            if not file_path.endswith('.txt'):
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            title = os.path.basename(file_path)
            return self.index_document(file_path, content, title)

        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return False

    def remove_document(self, file_path):
        """Удаление документа из индекса"""
        try:
            return self.data_service.delete_document(file_path)
        except Exception as e:
            logger.error(f"Ошибка удаления документа {file_path}: {e}")
            return False

    def search_with_gpt_fallback(self, query, top_k=10):
        """Search with GPT fallback when no documents are found"""
        try:
            # First, try regular search
            search_results = self.search(query, top_k)

            # If we found documents, return them
            if search_results:
                return {
                    'type': 'search_results',
                    'results': search_results,
                    'gpt_fallback_used': False
                }

            # If no documents found, use GPT fallback
            logger.info(f"No documents found for query: '{query}'. Using GPT fallback.")

            gpt_response = self._get_gpt_response(query)

            # Format GPT response as a "document"
            gpt_document = {
                'type': 'gpt_response',
                'results': [{
                    'doc_id': 'gpt-generated',
                    'title': f"AI Answer: {query}",
                    'file_path': 'ai-generated-response',
                    'score': 1.0,
                    'content_preview': gpt_response[:200] + '...' if len(gpt_response) > 200 else gpt_response,
                    'full_content': gpt_response,
                    'is_gpt_response': True
                }],
                'gpt_fallback_used': True
            }

            return gpt_document

        except Exception as e:
            logger.error(f"Error in search with GPT fallback: {e}")
            # Fallback to empty results if GPT also fails
            return {
                'type': 'error',
                'results': [],
                'gpt_fallback_used': False,
                'error': str(e)
            }

    def _get_gpt_response(self, query):
        """Get response from Ollama GPT model"""
        try:
            # Create a prompt that encourages concise, informative answers
            prompt = f"""Please provide a clear and concise answer to the following question. 
               If you're explaining a concept, give a brief definition and key characteristics.
               If it's a factual question, provide the most relevant information.

               Question: {query}

               Answer:"""

            response = self.ollama_client.generate(
                model=self.ollama_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'top_k': 40,
                    'top_p': 0.9,
                    'num_predict': 500  # Limit response length
                }
            )

            return response['response'].strip()

        except Exception as e:
            logger.error(f"Error getting GPT response: {e}")
            return f"I apologize, but I couldn't generate a response for your query '{query}'. Please try rephrasing your question or check if the Ollama service is running."

    def search(self, query, top_k=10):
        """Поиск документов по запросу"""
        try:
            # Предобработка запроса
            query_terms = self.preprocess_text(query)
            if not query_terms:
                return []

            # Получение всех документов
            documents = self.data_service.get_all_documents()
            avg_doc_length = self.data_service.get_avg_doc_length()

            # Расчет релевантности для каждого документа
            results = []
            for doc_id, file_path, last_modified in documents:
                doc_terms = self.data_service.get_document_terms(doc_id)
                doc_info = self.data_service.get_document_by_path(file_path)

                if not doc_info or not doc_terms:
                    continue

                doc_length = doc_info['doc_length'] or 0
                score = self.calculate_bm25_score(
                    doc_terms, query_terms, doc_length, avg_doc_length
                )

                if score > 0:
                    results.append({
                        'doc_id': doc_id,
                        'title': doc_info['title'],
                        'file_path': file_path,
                        'score': score,
                        'content_preview': doc_info['content'][:200] + '...'
                    })

            # Сортировка по релевантности
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []

    def calculate_metrics(self, query, relevant_docs):
        """Вычисление метрик качества (Precision, Recall, F1-score)"""
        search_results = self.search(query)
        retrieved_docs = {result['file_path'] for result in search_results}
        relevant_set = set(relevant_docs)

        # True Positives
        true_positives = retrieved_docs.intersection(relevant_set)

        # Precision
        precision = len(true_positives) / len(retrieved_docs) if retrieved_docs else 0

        # Recall
        recall = len(true_positives) / len(relevant_set) if relevant_set else 0

        # F1-score
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        return {
            'query': query,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'retrieved_count': len(retrieved_docs),
            'relevant_count': len(relevant_set),
            'true_positives': len(true_positives)
        }


if __name__ == "__main__":
    # Тестирование поискового сервиса
    db_config = {
        'dbname': 'search_system',
        'user': 'postgres',
        'password': '1234',
        'host': 'localhost',
        'port': '5432'
    }

    try:
        search_service = SearchService(db_config)
        print("✅ Поисковый сервис инициализирован")

        # Тест поиска
        results = search_service.search("dick", top_k=5)
        print(f"✅ Результаты поиска: {len(results)} документов найдено")
        for result in results:
            print(f"  - {result['title']} (score: {result['score']:.4f})")

        # Тест расчета метрик
        metrics = search_service.calculate_metrics(
            query="python programming",
            relevant_docs=["documents/test_document.txt"]
        )
        print(f"✅ Метрики качества:")
        print(f"  - Precision: {metrics['precision']:.4f}")
        print(f"  - Recall: {metrics['recall']:.4f}")
        print(f"  - F1-score: {metrics['f1_score']:.4f}")

        # Очистка тестовых данных
        search_service.remove_document("documents/test_document.txt")
        print("✅ Тестовые данные очищены")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")