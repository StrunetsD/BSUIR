import time
from idlelib.iomenu import encoding

import psycopg2
import os
import re
from collections import Counter
from typing import List, Dict, Tuple


class AlphabeticalProfileBuilder:
    """Alphabetical method language profile builder"""

    def __init__(self, conn, top_letters_count: int = 35):
        self.conn = conn
        self.top_letters_count = top_letters_count
        self.method = "alphabetical"
        self.profile_creation_time = {}

    def extract_letters(self, text: str) -> List[str]:
        """Extract letters from text"""
        cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', '', text.lower())
        return [char for char in cleaned_text if char.isalpha()]

    def calculate_frequencies(self, items: List[str]) -> List[Tuple[str, float]]:
        """Calculate frequencies for items"""
        if not items:
            return []

        counter = Counter(items)
        total_count = len(items)

        frequencies = []
        for item, count in counter.most_common():
            frequency = count / total_count
            frequencies.append((item, frequency))
        return frequencies

    def process_language_files(self, folder_path: str, language_id: str) -> List[str]:
        """Process all files for a specific language and return letters"""
        if not os.path.exists(folder_path):
            raise ValueError(f"Directory {folder_path} does not exist")

        all_letters = []

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)


            if os.path.isfile(file_path) and filename.endswith('.txt'):
                try:
                    file_encoding = "utf-8"
                    if language_id == "ru":
                        file_encoding = "windows-1251"
                    with open(file_path, 'r', encoding=file_encoding) as file:
                        text = file.read()

                    letters = self.extract_letters(text)
                    all_letters.extend(letters)

                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

        return all_letters

    def build_language_profile(self, folder_path: str, language_id: str):
        """Build alphabetical profile from folder and measure creation time"""
        start_time = time.time()

        all_letters = self.process_language_files(folder_path, language_id)

        if not all_letters:
            print(f"No letters found for language {language_id}")
            return

        letter_frequencies = self.calculate_frequencies(all_letters)
        top_letters = letter_frequencies[:self.top_letters_count]

        self.save_language_profile(language_id, top_letters)

        end_time = time.time()
        self.profile_creation_time[language_id] = end_time - start_time
        print(f"Profile for '{language_id}' created in {self.profile_creation_time[language_id]:.2f} seconds")

    def save_language_profile(self, language_id: str, letters: List[Tuple[str, float]]):
        """Save alphabetical profile to database"""
        if not letters:
            letters = []

        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM language_letters WHERE language_id = %s', (language_id,))

                for rank, (letter, frequency) in enumerate(letters, 1):
                    cursor.execute('''
                        INSERT INTO language_letters (language_id, letter, frequency, rank)
                        VALUES (%s, %s, %s, %s)
                    ''', (language_id, letter, frequency, rank))

                self.conn.commit()
                print(f"Alphabetical profile for '{language_id}' saved. Letters: {len(letters)}")

        except Exception as e:
            print(f"Error saving alphabetical profile for {language_id}: {e}")
            self.conn.rollback()

    def get_language_profile(self, language_id: str) -> List[Tuple[str, int, int]]:
        """Get alphabetical profile from database"""
        profile = []
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    SELECT letter, frequency, rank 
                    FROM language_letters 
                    WHERE language_id = %s 
                    ORDER BY rank
                ''', (language_id,))
                profile = cursor.fetchall()
        except Exception as e:
            print(f"Error getting alphabetical profile for {language_id}: {e}")
        return profile

    def detect(self, text: str) -> Dict:
        """Detect language using alphabetical method"""
        result = {
            'language': None,
            'confidence': 0.0,
            'method': self.method,
            'text_length': len(text),
        }

        letters = self.extract_letters(text)
        if not letters:
            return result

        text_letter_freq = dict(self.calculate_frequencies(letters))
        languages = {"ru", "eng"}

        best_language = None
        best_score = 0.0

        for lang_id in languages:
            score = self.calculate_similarity_score(lang_id, text_letter_freq)
            if score > best_score:
                best_score = score
                best_language = lang_id

        result['language'] = best_language
        result['confidence'] = best_score

        return result

    def calculate_similarity_score(self, language_id: str, text_frequencies: Dict[str, float]) -> float:
        """Calculate similarity score between text and language profile"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    SELECT letter, frequency FROM language_letters 
                    WHERE language_id = %s ORDER BY rank
                ''', (language_id,))

                lang_frequencies = {row[0]: float(row[1]) for row in cursor.fetchall()}
                common_letters = set(text_frequencies.keys()) & set(lang_frequencies.keys())

                if not common_letters:
                    return 0.0

                dot_product = sum(text_frequencies[letter] * lang_frequencies[letter]
                                  for letter in common_letters)

                text_norm = sum(freq ** 2 for freq in text_frequencies.values()) ** 0.5
                lang_norm = sum(freq ** 2 for freq in lang_frequencies.values()) ** 0.5

                if text_norm == 0 or lang_norm == 0:
                    return 0.0

                return dot_product / (text_norm * lang_norm)

        except Exception as e:
            print(f"Error calculating similarity for {language_id}: {e}")
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
        ngram_builder = AlphabeticalProfileBuilder(conn, top_letters_count=40)

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
            "Привет мир, как дела у вас сегодня?  я искренне не понимаю почему он определяет язык с такой уверенностью мкумукацк ацакй ак  как пке  рпо пву ивуцш оп ирйсьвлойзменйимрсолыйкгмйрнгисйовлйзмикшукйзимвомийзм",
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