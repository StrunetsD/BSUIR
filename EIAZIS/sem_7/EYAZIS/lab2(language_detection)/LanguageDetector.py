import time
import psycopg2
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from html.parser import HTMLParser
import pickle
import os


# Data class для стандартизации результатов
@dataclass
class DetectionResult:
    """Data class to standardize detection results"""
    method: str
    language: str
    confidence: float
    details: Dict[str, Any]
    processing_time: float


# HTML парсер для извлечения текста
class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = {'script', 'style', 'meta', 'link', 'head'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags and data.strip():
            self.text.append(data.strip())

    def get_text(self):
        return ' '.join(self.text)


# Основной сервис
class LanguageDetectionService:
    def __init__(self,
                 db_config: Dict[str, Any],
                 alphabetical_detector_,  # Уже реализованный алфавитный детектор
                 ngram_detector_,  # Уже реализованный n-gram детектор
                 neural_detector_,  # Уже реализованный нейросетевой детектор
                 neural_model_path: str = None,
                 neural_vocab_path: str = None):

        self.db_conn = self._init_db_connection(db_config)
        self.alphabetical_detector = alphabetical_detector_
        self.ngram_detector = ngram_detector_
        self.neural_detector = neural_detector_

        # Инициализация детекторов с подключением к БД
        self._initialize_detectors()

    def _init_db_connection(self, db_config: Dict[str, Any]):
        """Initialize database connection"""
        try:
            return psycopg2.connect(**db_config)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    def _initialize_detectors(self):
        """Initialize detectors with database connection"""
        # Если детекторы требуют подключения к БД, передаем его
        if hasattr(self.alphabetical_detector, 'conn'):
            self.alphabetical_detector.conn = self.db_conn
        if hasattr(self.ngram_detector, 'conn'):
            self.ngram_detector.conn = self.db_conn

    def parse_html(self, html_content: str) -> str:
        """Extract clean text from HTML using HTMLParser"""
        extractor = HTMLTextExtractor()
        extractor.feed(html_content)
        return extractor.get_text()

    def detect_from_html_content(self, html_content: str) -> List[DetectionResult]:
        """Detect language from HTML content string"""
        clean_text = self.parse_html(html_content)

        if not clean_text.strip():
            raise ValueError("No text content found in HTML")

        return self._run_detection_methods(clean_text)

    def detect_from_html_file(self, html_file_path: str) -> List[DetectionResult]:
        """Detect language from HTML file path"""
        # Чтение HTML файла
        with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        return self.detect_from_html_content(html_content)

    def _run_detection_methods(self, clean_text: str) -> List[DetectionResult]:
        """Run all detection methods on clean text"""
        results = []

        # Алфавитный метод
        results.append(self._run_alphabetical_detection(clean_text))

        # N-gram метод
        results.append(self._run_ngram_detection(clean_text))

        # Нейросетевой метод
        results.append(self._run_neural_detection(clean_text))

        return results

    def _run_alphabetical_detection(self, text: str) -> DetectionResult:
        """Run alphabetical detection method"""
        start_time = time.time()

        try:
            # Используем существующий метод detect
            raw_result = self.alphabetical_detector.detect(text)

            # Конвертируем в стандартный формат
            return DetectionResult(
                method="alphabetical",
                language=raw_result.get('language', 'unknown'),
                confidence=raw_result.get('confidence', 0.0),
                details={
                    'text_length': raw_result.get('text_length', len(text)),
                },
                processing_time=time.time() - start_time
            )
        except Exception as e:
            return DetectionResult(
                method="alphabetical",
                language="unknown",
                confidence=0.0,
                details={"error": str(e)},
                processing_time=time.time() - start_time
            )

    def _run_ngram_detection(self, text: str) -> DetectionResult:
        """Run n-gram detection method"""
        start_time = time.time()

        try:
            # Используем существующий метод detect
            raw_result = self.ngram_detector.detect(text)

            # Конвертируем в стандартный формат
            return DetectionResult(
                method="n-gram",
                language=raw_result.get('language', 'unknown'),
                confidence=raw_result.get('confidence', 0.0),
                details={
                    'text_length': raw_result.get('text_length', len(text)),
                    'n_gram_size': getattr(self.ngram_detector, 'n_gram_size', 3),
                },
                processing_time=time.time() - start_time
            )
        except Exception as e:
            return DetectionResult(
                method="n-gram",
                language="unknown",
                confidence=0.0,
                details={"error": str(e)},
                processing_time=time.time() - start_time
            )

    def _run_neural_detection(self, text: str) -> DetectionResult:
        """Run neural network detection method"""
        start_time = time.time()
        raw_result = None
        try:
            # Используем существующий метод detect
            # Предполагаем, что нейросетевой детектор имеет метод detect или используется через функцию
            if hasattr(self.neural_detector, 'detect'):
                raw_result = self.neural_detector.detect(text)

            print(raw_result)
            # Конвертируем в стандартный формат
            return DetectionResult(
                method="neural",
                language=raw_result.get('language', 'unknown'),
                confidence=raw_result.get('confidence', 0.0),
                details={
                    'text_length': len(text),
                    'method_specific': {k: v for k, v in raw_result.items()
                                        if k not in ['method', 'language', 'confidence']}
                },
                processing_time=time.time() - start_time
            )
        except Exception as e:
            return DetectionResult(
                method="neural",
                language="unknown",
                confidence=0.0,
                details={"error": str(e)},
                processing_time=time.time() - start_time
            )

    def get_detection_summary(self, results: List[DetectionResult]) -> Dict[str, Any]:
        """Get summary of all detection results"""
        summary = {
            "total_methods": len(results),
            "successful_detections": 0,
            "languages_detected": set(),
            "average_confidence": 0.0,
            "fastest_method": None,
            "results": []
        }

        total_confidence = 0.0
        fastest_time = float('inf')

        for result in results:
            # Конвертируем в словарь для сериализации
            result_dict = asdict(result)
            summary["results"].append(result_dict)

            if result.language != "unknown":
                summary["successful_detections"] += 1
                summary["languages_detected"].add(result.language)
                total_confidence += result.confidence

            if result.processing_time < fastest_time:
                fastest_time = result.processing_time
                summary["fastest_method"] = result.method

        if summary["successful_detections"] > 0:
            summary["average_confidence"] = total_confidence / summary["successful_detections"]

        summary["languages_detected"] = list(summary["languages_detected"])

        return summary

    def close(self):
        """Close database connection"""
        if hasattr(self, 'db_conn') and self.db_conn:
            self.db_conn.close()


# Пример использования с существующими детекторами
if __name__ == "__main__":
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'lang_detection',
        'user': 'postgres',
        'password': '1234'
    }

    # Предполагаем, что детекторы уже созданы
    from build_profile_ngram import NGramProfileBuilder
    from build_profiles_for_alphabet_alg import AlphabeticalProfileBuilder
    from Neural_lang_detector import load_trained_model

    # Инициализация существующих детекторов
    alphabetical_detector = AlphabeticalProfileBuilder(None)
    ngram_detector = NGramProfileBuilder(None)
    neural_detector = load_trained_model('trained_model.pth', 'vocabulary.pkl')

    # Создание сервиса
    service = LanguageDetectionService(
        db_config=DB_CONFIG,
        alphabetical_detector_=alphabetical_detector,
        ngram_detector_=ngram_detector,
        neural_detector_=neural_detector
    )

    try:
        # Пример определения языка из файла
        results = service.detect_from_html_file('english_page.html')

        # Вывод результатов
        for result in results:
            print(f"Method: {result.method}")
            print(f"Language: {result.language}")
            print(f"Confidence: {result.confidence:.4f}")
            print(f"Processing time: {result.processing_time:.4f}s")
            print(f"Details: {result.details}")
            print("-" * 50)

        # Сводка
        summary = service.get_detection_summary(results)
        print("\nSummary:")
        print(f"Languages detected: {summary['languages_detected']}")
        print(f"Average confidence: {summary['average_confidence']:.4f}")
        print(f"Fastest method: {summary['fastest_method']}")

    finally:
        service.close()