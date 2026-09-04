import time
import psycopg2
import os
import re
from collections import Counter
from typing import List, Dict, Tuple


class NGramProfileBuilder:
    """N-gram based language profile builder with detection capability"""

    def __init__(self, conn, n_gram_size: int = 3, top_ngrams_count: int = 500):
        self.conn = conn
        self.n_gram_size = n_gram_size
        self.top_ngrams_count = top_ngrams_count
        self.method = "n-gram"
        self.profile_creation_time = {}


    def extract_ngrams(self, text: str, n: int) -> List[str]:
        """Extract N-grams from text"""
        cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', '', text.lower())

        ngrams = []
        for i in range(len(cleaned_text) - n + 1):
            ngram = cleaned_text[i:i + n]
            if ngram.strip():
                ngrams.append(ngram)

        return ngrams

    def process_language_files(self, folder_path: str, language_id: str) -> List[str]:
        """Process all files for a specific language and return ngrams"""
        if not os.path.exists(folder_path):
            raise ValueError(f"Directory {folder_path} does not exist")

        all_ngrams = []

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if os.path.isfile(file_path) and filename.endswith('.txt'):
                try:
                    file_encoding = "utf-8"
                    if language_id == "ru":
                        file_encoding = "windows-1251"
                    with open(file_path, 'r', encoding=file_encoding) as file:
                        text = file.read()

                    ngrams = self.extract_ngrams(text, self.n_gram_size)
                    all_ngrams.extend(ngrams)

                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

        return all_ngrams

    def build_language_profile(self, folder_path: str, language_id: str):
        """Build language profile from folder and measure creation time"""
        start_time = time.time()

        ngrams = self.process_language_files(folder_path, language_id)

        if not ngrams:
            print(f"No N-grams found for language {language_id}")
            return

        ngram_freq = Counter(ngrams)
        top_ngrams = ngram_freq.most_common(self.top_ngrams_count)
        self.save_language_profile(language_id, top_ngrams)

        end_time = time.time()
        self.profile_creation_time[language_id] = end_time - start_time
        print(f"Profile for '{language_id}' created in {self.profile_creation_time[language_id]:.2f} seconds")

    def save_language_profile(self, language_id: str, ngrams: List[Tuple[str, int]]):
        """Save N-gram profile to database"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM language_ngrams WHERE language_id = %s', (language_id,))

                for rank, (ngram, frequency) in enumerate(ngrams, 1):
                    cursor.execute('''
                        INSERT INTO language_ngrams (language_id, ngram, frequency, rank)
                        VALUES (%s, %s, %s, %s)
                    ''', (language_id, ngram, frequency, rank))

                self.conn.commit()
                print(f"N-gram profile for '{language_id}' saved. Processed {len(ngrams)} N-grams")

        except Exception as e:
            print(f"Error saving N-gram profile for {language_id}: {e}")
            self.conn.rollback()

    def get_language_profile(self, language_id: str) -> List[Tuple[str, int, int]]:
        """Get N-gram profile from database"""
        profile = []
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    SELECT ngram, frequency, rank 
                    FROM language_ngrams 
                    WHERE language_id = %s 
                    ORDER BY rank
                ''', (language_id,))
                profile = cursor.fetchall()
        except Exception as e:
            print(f"Error getting N-gram profile for {language_id}: {e}")
        return profile

    def detect(self, text: str) -> Dict:
        """Detect language using N-gram method"""
        result = {
            'language': None,
            'confidence': 0.0,
            'method': self.method,
            'text_length': len(text),
        }

        if not text or len(text.strip()) < self.n_gram_size:
            return result

        # Extract ngrams from input text
        text_ngrams = self.extract_ngrams(text, self.n_gram_size)
        if not text_ngrams:
            return result

        text_ngram_freq = Counter(text_ngrams)
        text_total = len(text_ngrams)

        # Get available languages
        languages = {"ru", "eng"}
        if not languages:
            return result

        best_language = None
        best_score = 0.0

        for lang_id in languages:
            score = self.calculate_ngram_similarity(lang_id, text_ngram_freq, text_total)
            if score > best_score:
                best_score = score
                best_language = lang_id


        result['language'] = best_language
        result['confidence'] = best_score

        return result

    # def calculate_ngram_similarity(self, language_id: str, text_ngram_freq: Dict[str, int], text_total: int ) -> float:
    #     """Calculate raw weighted score based on rank"""
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute('''
    #                 SELECT ngram, frequency, rank
    #                 FROM language_ngrams
    #                 WHERE language_id = %s
    #                 ORDER BY rank
    #             ''', (language_id,))
    #
    #             lang_profile = cursor.fetchall()
    #             if not lang_profile:
    #                 return 0.0
    #
    #             raw_score = 0.0
    #
    #             for ngram, lang_freq, rank in lang_profile[:self.top_ngrams_count]:
    #                 if ngram in text_ngram_freq:
    #
    #                     points = self.top_ngrams_count - rank
    #                     raw_score += points
    #
    #             return raw_score / text_total
    #
    #     except Exception as e:
    #         print(f"Error calculating N-gram similarity for {language_id}: {e}")
    #         return 0.0

    def calculate_ngram_similarity(self, language_id: str, text_ngram_freq: Dict[str, int], text_total: int) -> float:
        """Calculate confidence as percentage of matching n-grams with rank weighting"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    SELECT ngram, frequency, rank 
                    FROM language_ngrams 
                    WHERE language_id = %s 
                    ORDER BY rank
                ''', (language_id,))

                lang_profile = cursor.fetchall()
                if not lang_profile:
                    return 0.0

                total_possible_score = 0
                actual_score = 0
                matched_ngrams = 0

                for ngram, freq, rank in lang_profile[:self.top_ngrams_count]:
                    # Weight by rank (higher rank = more valuable match)
                    weight = self.top_ngrams_count - rank + 1
                    total_possible_score += weight

                    if ngram in text_ngram_freq:
                        actual_score += weight
                        matched_ngrams += 1

                if total_possible_score == 0:
                    return 0.0

                confidence_percentage = (actual_score / total_possible_score)

                return confidence_percentage

        except Exception as e:
            print(f"Error calculating N-gram similarity for {language_id}: {e}")
            return 0.0

    def get_profile_creation_time(self, language_id: str = None) -> float:
        """Get profile creation time for a language or average if no language specified"""
        if language_id:
            return self.profile_creation_time.get(language_id, 0.0)
        elif self.profile_creation_time:
            return sum(self.profile_creation_time.values()) / len(self.profile_creation_time)
        return 0.0


def main():
    # Database connection parameters
    db_params = {
        'host': 'localhost',
        'database': 'lang_detection',
        'user': 'postgres',
        'password': '1234',
        'port': 5432
    }

    try:
        # Establish database connection
        conn = psycopg2.connect(**db_params)
        print("Connected to database successfully!")

        # Initialize NGramProfileBuilder
        ngram_builder = NGramProfileBuilder(conn, n_gram_size=3, top_ngrams_count=500)

        # Build language profiles
        print("\n=== Building Language Profiles ===")

        # Build Russian profile (assuming files are in windows-1251 encoding)
        russian_folder = "russian_files"  # Path to folder with Russian text files
        ngram_builder.build_language_profile(russian_folder, "ru")

        # Build English profile
        english_folder = "english_files"  # Path to folder with English text files
        ngram_builder.build_language_profile(english_folder, "eng")

        # Display profile creation times
        print(f"\n=== Profile Creation Times ===")
        print(f"Russian profile: {ngram_builder.get_profile_creation_time('ru'):.2f} seconds")
        print(f"English profile: {ngram_builder.get_profile_creation_time('eng'):.2f} seconds")
        print(f"Average: {ngram_builder.get_profile_creation_time():.2f} seconds")

        # Test language detection
        print("\n=== Language Detection Tests ===")

        test_texts = [
            "Привет мир, как дела у вас сегодня? Воронов посмотрел на город, на поляну, где расстреливали солдатика, перекрестился и ползком, между кустарниками, дрожа от страха, добрался до лесу…Перед ним открывалась бесконечная лесная трущоба.Воронов обернулся назад и посмотрел в сторону города. я искренне не понимаю почему он определяет язык с такой уверенностью ",
            "Bonjour le monde, comment allez-vous aujourd'hui?",
            "Hola mundo, ¿cómo estás hoy?",
            "Это пример русского текста для проверки работы системы определения языка",
            "This is an example English text to test the language detection system",
            "Hello world, how are you doing today?"

        ]

        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}:")
            print(f"Text: {text[:50]}...")
            result = ngram_builder.detect(text)
            print(f"Detected language: {result['language']}")
            print(f"Confidence: {result['confidence']:.4f}")
            print(f"Method: {result['method']}")
            print(f"Text length: {result['text_length']}")

        # Retrieve and display profile information
        print("\n=== Language Profile Information ===")
        languages = ["ru", "eng"]

        for lang in languages:
            profile = ngram_builder.get_language_profile(lang)
            print(f"\n{lang.upper()} profile has {len(profile)} n-grams")
            if profile:
                print("Top 5 n-grams:")
                for ngram, freq, rank in profile[:5]:
                    print(f"  Rank {rank}: '{ngram}' (frequency: {freq})")

    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close database connection
        if 'conn' in locals():
            conn.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()