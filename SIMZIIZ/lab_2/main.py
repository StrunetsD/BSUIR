import time
from collections import Counter

class VigenereCipher:
    def __init__(self):
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 0123456789.,!?;:'\"-()"
        self.char_to_num = {char: idx for idx, char in enumerate(self.alphabet)}
        self.num_to_char = {idx: char for idx, char in enumerate(self.alphabet)}
        self.alphabet_size = len(self.alphabet)
        
        self.common_words = {
            'the', 'and', 'you', 'that', 'was', 'for', 'are', 'with', 'his', 'they',
            'this', 'have', 'from', 'one', 'had', 'word', 'but', 'not', 'what', 'all',
            'were', 'when', 'your', 'can', 'said', 'there', 'use', 'each', 'which', 'she',
            'how', 'their', 'will', 'other', 'about', 'out', 'many', 'then', 'them', 'these',
            'so', 'some', 'her', 'would', 'make', 'like', 'him', 'into', 'time', 'has'
        }
    
    def encrypt(self, plaintext, key):
        """Шифрование текста"""
        encrypted = []
        key_len = len(key)
        
        for i, char in enumerate(plaintext):
            if char not in self.char_to_num:
                encrypted.append(char)
                continue
                
            text_num = self.char_to_num[char]
            key_num = self.char_to_num[key[i % key_len]]
            encrypted_num = (text_num + key_num) % self.alphabet_size
            encrypted.append(self.num_to_char[encrypted_num])
        
        return ''.join(encrypted)
    
    def decrypt(self, ciphertext, key):
        """Дешифрование текста"""
        decrypted = []
        key_len = len(key)
        
        for i, char in enumerate(ciphertext):
            if char not in self.char_to_num:
                decrypted.append(char)
                continue
                
            text_num = self.char_to_num[char]
            key_num = self.char_to_num[key[i % key_len]]
            decrypted_num = (text_num - key_num) % self.alphabet_size
            decrypted.append(self.num_to_char[decrypted_num])
        
        return ''.join(decrypted)
    
    def is_likely_english(self, text):
        """Проверяет, похож ли текст на английский"""
        if len(text) < 10:
            return False
        
        text_lower = text.lower()
        words = text_lower.split()
        
        common_word_count = sum(1 for word in words if word in self.common_words)
        if common_word_count >= 2:
            return True
        
        freq = Counter(text_lower)
        total_letters = sum(freq.get(char, 0) for char in 'abcdefghijklmnopqrstuvwxyz')
        
        if total_letters < 5:
            return False
        
        common_letters = 'etaoinshrdlc'
        common_count = sum(freq.get(char, 0) for char in common_letters)
        
        rare_letters = 'zjqxkv'
        rare_count = sum(freq.get(char, 0) for char in rare_letters)
        
        return (common_count / total_letters > 0.5 and 
                rare_count / total_letters < 0.1)
    
    def generate_keys(self, key_length):
        """Генератор ключей заданной длины"""
        from itertools import product
        
        for key_chars in product(self.alphabet, repeat=key_length):
            yield ''.join(key_chars)
    
    def brute_force_attack(self, ciphertext, max_key_length=4, known_plaintext=None):
        """Атака полным перебором ключей"""
        print(f" Начинаем атаку полным перебором...")
        print(f"Длина зашифрованного текста: {len(ciphertext)} символов")
        print(f"Максимальная длина ключа: {max_key_length}")
        print(f"Размер алфавита: {self.alphabet_size} символов")
        print("-" * 50)
        
        start_time = time.time()
        tested_keys = 0
        found_keys = []
        
        for key_length in range(1, max_key_length + 1):
            print(f"\n Поиск ключей длины {key_length}...")
            total_keys = self.alphabet_size ** key_length
            print(f"Всего возможных ключей: {total_keys:,}")
            
            key_gen = self.generate_keys(key_length)
            batch_size = min(1000, total_keys)
            
            for i in range(batch_size):
                try:
                    key = next(key_gen)
                except StopIteration:
                    break
                
                tested_keys += 1
                decrypted = self.decrypt(ciphertext, key)
                
                if known_plaintext and known_plaintext.lower() in decrypted.lower():
                    found_keys.append((key, decrypted))
                    print(f" Найден ключ: '{key}' (по известному фрагменту)")
                    if len(found_keys) >= 3:
                        break
                
                elif not known_plaintext and self.is_likely_english(decrypted):
                    found_keys.append((key, decrypted))
                    print(f" Найден потенциальный ключ: '{key}'")
                    print(f"   Текст: '{decrypted[:50]}...'")
                    if len(found_keys) >= 3:
                        break
                
                if total_keys > 1000 and i % 100 == 0:
                    print(f"Проверено {i}/{batch_size} ключей...")
            
            if found_keys:
                break
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n{'='*50}")
        print("РЕЗУЛЬТАТЫ АТАКИ:")
        print(f"Проверено ключей: {tested_keys:,}")
        print(f"Затраченное время: {elapsed_time:.2f} секунд")
        print(f"Скорость: {tested_keys/elapsed_time:.0f} ключей/сек")
        
        if found_keys:
            print(f"\nНайдено потенциальных ключей: {len(found_keys)}")
            for i, (key, decrypted) in enumerate(found_keys, 1):
                print(f"\n{i}. Ключ: '{key}'")
                print(f"   Расшифрованный текст: '{decrypted}'")
            
            return found_keys
        else:
            print("\n Ключ не найден. Попробуйте:")
            print("   - Увеличить максимальную длину ключа")
            print("   - Указать известный фрагмент текста")
            print("   - Использовать более длинный зашифрованный текст")
            return None
    
    def estimate_attack_time(self, key_length):
        """Оценка времени для атаки перебором"""
        total_keys = self.alphabet_size ** key_length
        keys_per_second = 1000  
        
        seconds = total_keys / keys_per_second
        
        if seconds < 60:
            return f"{seconds:.1f} секунд"
        elif seconds < 3600:
            return f"{seconds/60:.1f} минут"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} часов"
        elif seconds < 31536000:
            return f"{seconds/86400:.1f} дней"
        else:
            return f"{seconds/31536000:.1f} лет"

print("ШИФР ВИЖЕНЕРА: АНАЛИЗ И РЕАЛИЗАЦИЯ")
print("=" * 60)

cipher = VigenereCipher()

test_text = "Hello World this is a secret message"
test_key = "key"

print("Тестовое шифрование:")
print(f"Исходный текст: '{test_text}'")
print(f"Ключ: '{test_key}'")

# 
encrypted = cipher.encrypt(test_text, test_key)
print(f"Зашифрованный текст: '{encrypted}'")

decrypted = cipher.decrypt(encrypted, test_key)
print(f"Расшифрованный текст: '{decrypted}'")
print()

print("Оценка времени атаки перебором:")
for key_len in range(1, 5):
    time_estimate = cipher.estimate_attack_time(key_len)
    keys_count = cipher.alphabet_size ** key_len
    print(f"Длина ключа {key_len}: {keys_count:,} ключей, время: {time_estimate}")

print()

print(" Демонстрация атаки перебором (ключ длины 2):")
short_key = "ab"
test_message = "Secret message"
short_encrypted = cipher.encrypt(test_message, short_key)

print(f"Исходное сообщение: '{test_message}'")
print(f"Ключ: '{short_key}'")
print(f"Зашифрованный текст: '{short_encrypted}'")

result = cipher.brute_force_attack(short_encrypted, max_key_length=2)
if result:
    if isinstance(result, list) and len(result) > 1:
        print(f"\n Найдено несколько возможных ключей ({len(result)}).")
        print("Первый найденный ключ:")
        found_key, found_text = result[0]
    else:
        found_key, found_text = result
    
    print(f" Найден ключ: '{found_key}'")
    print(f"Расшифрованный текст: '{found_text}'")
    
    if found_text == test_message:
        print(" Ключ найден верно!")
    else:
        print(" Найден неверный ключ (ложное срабатывание)")
else:
    print(" Ключ не найден")