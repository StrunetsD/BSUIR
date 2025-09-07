import random
import math
import os

# Стандартные числа Ферма, часто используемые в RSA как публичная экспонента
FERMAT_NUMBERS = [65537, 257, 17]

def read_file(filename):
    """Чтение содержимого файла с обработкой отсутствия файла"""
    if not os.path.exists(filename):
        return ""
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    return data

def write_file(filename, message):
    """Запись сообщения в файл с указанной кодировкой"""
    with open(filename, "w", encoding='utf-8') as f:
        f.write(message)

def exponentiation(x, degree, p):
    """Быстрое возведение в степень по модулю (метод возведения в степень по модулю через двоичное разложение)"""
    result = 1
    x = x % p  # Нормализуем x по модулю p
    while degree > 0:
        if degree % 2 == 1:  # Если степень нечётная
            result = (result * x) % p
        degree = degree >> 1  # Эквивалентно целочисленному делению на 2
        x = (x * x) % p  # Возводим x в квадрат по модулю p
    return result

def is_prime(n, k=5):
    """Проверка числа на простоту с использованием теста Миллера-Рабина"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:  # Чётные числа больше 2 не простые
        return False
    
    # Представляем n-1 в виде (2^r)*d
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    
    # Проводим k тестов для увеличения достоверности
    for _ in range(k):
        a = random.randint(2, n-2)
        x = pow(a, d, n)  # a^d mod n
        if x == 1 or x == n-1:
            continue
        for _ in range(r-1):
            x = pow(x, 2, n)
            if x == n-1:
                break
        else:
            return False  # Число составное
    return True  # Вероятно простое

def generate_large_prime(bits=512):
    """Генерация большого простого числа заданной битности"""
    while True:
        num = random.getrandbits(bits)
        num |= (1 << bits - 1) | 1  # Устанавливаем старший бит в 1 для нужной длины и делаем нечётным
        if is_prime(num):
            return num

def extended_gcd(a, b):
    """Расширенный алгоритм Евклида для нахождения НОД и коэффициентов Безу"""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def multiplicative_reciprocal(e, e_func):
    """Нахождение обратного элемента по модулю с использованием расширенного алгоритма Евклида"""
    gcd, x, y = extended_gcd(e, e_func)
    if gcd != 1:
        raise ValueError("Обратный элемент не существует")
    return x % e_func  # Нормализуем результат к положительному значению

def create_keys():
    """Создание пары ключей RSA (публичный и приватный)"""
    print("Генерация простых чисел p и q...")
    p = generate_large_prime(256)  # 256-битные простые числа
    q = generate_large_prime(256)
    
    while p == q:  # Гарантируем, что p и q разные
        q = generate_large_prime(256)
    
    n = p * q  # Модуль RSA
    e_func = (p - 1) * (q - 1)  # Функция Эйлера
    
    # Выбираем публичную экспоненту из чисел Ферма
    e = 0
    for number in FERMAT_NUMBERS:
        if math.gcd(number, e_func) == 1:
            e = number
            break
    
    # Если ни одно число Ферма не подошло, ищем ближайшее подходящее
    if e == 0:
        e = 65537
        while math.gcd(e, e_func) != 1:
            e += 2
    
    # Вычисляем секретную экспоненту
    d = multiplicative_reciprocal(e, e_func)
    
    # Сохраняем ключи в файлы
    write_file("open_key.txt", f"{n},{e}")
    write_file("secret_key.txt", f"{n},{d}")
    
    print(f"✓ Ключи созданы:")
    print(f"p = {p}")
    print(f"q = {q}")
    print(f"n = {n}")
    print(f"e = {e}")
    print(f"d = {d}")

def create_test_message():
    """Создание тестового сообщения для шифрования"""
    message = "123456789"  # Тестовое сообщение должно быть числом
    write_file("orig_mes.txt", message)
    print(f" Создано тестовое сообщение: {message}")

def message_encryption():
    """Шифрование сообщения с использованием публичного ключа"""
    try:
        message_text = read_file("orig_mes.txt")
        if not message_text:
            print("Файл orig_mes.txt пуст или не существует")
            return
        
        message = int(message_text)  # Сообщение должно быть числом
        key_data = read_file("open_key.txt")
        if not key_data:
            print("Файл open_key.txt не существует. Сначала создайте ключи.")
            return
            
        n, e = key_data.split(",")
        # Шифрование: c = m^e mod n
        c = exponentiation(message, int(e), int(n))
        write_file("encr_mes.txt", f"{c}")
        print(f"Сообщение зашифровано: {c}")
    except ValueError:
        print("Ошибка: Сообщение должно быть числом")
    except Exception as e:
        print(f"Ошибка при шифровании: {e}")

def message_decryption():
    """Дешифрование сообщения с использованием приватного ключа"""
    try:
        cipher_text = read_file("encr_mes.txt")
        if not cipher_text:
            print("Файл encr_mes.txt пуст или не существует")
            return
            
        c = int(cipher_text)
        key_data = read_file("secret_key.txt")
        if not key_data:
            print("Файл secret_key.txt не существует")
            return
            
        n, d = key_data.split(",")
        # Дешифрование: m = c^d mod n
        m = exponentiation(c, int(d), int(n))
        write_file("decr_mes.txt", f"{m}")
        print(f"✓ Сообщение расшифровано: {m}")
        
        # Сравниваем с оригиналом для проверки
        original = read_file("orig_mes.txt")
        if original and int(original) == m:
            print(" Расшифрованное сообщение совпадает с исходным")
        else:
            print(" Расшифрованное сообщение не совпадает с исходным")
            
    except Exception as e:
        print(f"Ошибка при дешифровании: {e}")

def signature_encryption():
    """Создание электронной подписи с использованием приватного ключа"""
    try:
        message_text = read_file("orig_mes.txt")
        if not message_text:
            print("Файл orig_mes.txt пуст или не существует")
            return None, None
            
        m = int(message_text)
        key_data = read_file("secret_key.txt")
        if not key_data:
            print("Файл secret_key.txt не существует")
            return None, None
            
        n, d = key_data.split(",")
        # Создание подписи: s = m^d mod n
        s = exponentiation(m, int(d), int(n))
        write_file("signature.txt", f"{s}")
        print(f" Создана подпись: {s}")
        return s, m
    except Exception as e:
        print(f"Ошибка при создании подписи: {e}")
        return None, None

def signature_decryption():
    """Проверка электронной подписи с использованием публичного ключа"""
    try:
        s, m = signature_encryption()
        if s is None:
            return
            
        key_data = read_file("open_key.txt")
        if not key_data:
            print("Файл open_key.txt не существует")
            return
            
        n, e = key_data.split(",")
        # Проверка подписи: m2 = s^e mod n
        m2 = exponentiation(int(s), int(e), int(n))
        
        print(f" Проверка подписи:")
        print(f"Исходное сообщение: {m}")
        print(f"Восстановленное сообщение: {m2}")
        
        # Сравниваем восстановленное сообщение с оригиналом
        if m2 == m:
            print("✓ ЭЦП соответствует - подпись верна")
        else:
            print("✗ ЭЦП не соответствует - подпись неверна")
    except Exception as e:
        print(f"Ошибка при проверке подписи: {e}")

def main():
    """Основная функция, управляющая всем процессом"""
    print(" RSA ШИФРОВАНИЕ С ЭЛЕКТРОННОЙ ПОДПИСЬЮ")
    print("=" * 50)
    
    # Создаем тестовое сообщение
    create_test_message()
    
    # Создаем ключи
    print("\n1. Создание ключей RSA...")
    create_keys()
    
    # Шифруем сообщение
    print("\n2. Шифрование сообщения...")
    message_encryption()
    
    # Дешифруем сообщение
    print("\n3. Дешифрование сообщения...")
    message_decryption()
    
    # Проверяем электронную подпись
    print("\n4. Проверка электронной подписи...")
    signature_decryption()
    
    print("\n" + "=" * 50)
    print("Все файлы созданы:")
    print("- orig_mes.txt - исходное сообщение")
    print("- open_key.txt - открытый ключ (n, e)")
    print("- secret_key.txt - закрытый ключ (n, d)")
    print("- encr_mes.txt - зашифрованное сообщение")
    print("- decr_mes.txt - расшифрованное сообщение")
    print("- signature.txt - электронная подпись")

if __name__ == "__main__":
    main()