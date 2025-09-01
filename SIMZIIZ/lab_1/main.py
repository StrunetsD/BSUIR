import random
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import string
import os

RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"

def generate_string(length):
    """Генерация случайной строки заданной длины"""
    return ''.join(random.choice(RUSSIAN_ALPHABET) for _ in range(length))

def analyze_distribution(input_str):
    """Анализ распределения символов в строке"""
    total = len(input_str)
    freq = Counter(input_str)
    
    print("\nЧастотное распределение символов:")
    print("Символ\tКоличество\tПроцент\tГистограмма")
    
    max_freq = max(freq.values()) if freq else 1
    
    for char, count in sorted(freq.items()):
        percentage = (count / total) * 100
        bar_length = int((count / max_freq) * 50)
        print(f"{char}\t{count}\t\t{percentage:.2f}%\t{'*' * bar_length}")

def measure_crack_time(password, iterations=5):
    """Измерение времени подбора пароля"""
    total_time = 0
    alphabet_size = len(RUSSIAN_ALPHABET)
    
    for _ in range(iterations):
        start_time = time.time()
        attempts = 0
        found = False
        
        # Ограничиваем максимальное количество попыток
        max_attempts = min(100000, alphabet_size ** len(password) // 100)
        
        while attempts < max_attempts and not found:
            attempt = ''.join(random.choice(RUSSIAN_ALPHABET) for _ in range(len(password)))
            attempts += 1
            
            if attempt == password:
                found = True
        
        end_time = time.time()
        total_time += (end_time - start_time)
    
    return total_time / iterations

def format_time(seconds):
    """Форматирование времени в читаемый вид"""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f} наносекунд"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f} микросекунд"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} миллисекунд"
    elif seconds < 60:
        return f"{seconds:.2f} секунд"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} минут"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.2f} часов"
    elif seconds < 31536000:
        days = seconds / 86400
        return f"{days:.2f} дней"
    else:
        years = seconds / 31536000
        return f"{years:.2f} лет"

def calculate_theoretical_time(password_length, attempts_per_second=1000000):
    """Вычисление теоретического времени подбора"""
    alphabet_size = len(RUSSIAN_ALPHABET)
    total_combinations = alphabet_size ** password_length
    average_time = total_combinations / (2 * attempts_per_second)  # В среднем нужно проверить половину
    
    return average_time, total_combinations

def generate_time_graph(max_length, filename=None):
    """Генерация графика зависимости времени подбора от длины пароля"""
    lengths = list(range(1, max_length + 1))
    times = []
    theoretical_times = []
    
    print("Генерация данных для графика...")
    print("Длина\tЭксп. время\tТеор. время\tКомбинации")
    print("-" * 60)
    
    for length in lengths:
        password = generate_string(length)
        avg_time = measure_crack_time(password, iterations=3)
        times.append(avg_time)
        
        theoretical_time, combinations = calculate_theoretical_time(length)
        theoretical_times.append(theoretical_time)
        
        print(f"{length}\t{format_time(avg_time)}\t{format_time(theoretical_time)}\t{combinations:,}")
    
    # Построение графика
    plt.figure(figsize=(12, 8))
    
    # Экспериментальные данные
    plt.plot(lengths, times, 'bo-', linewidth=2, markersize=8, label='Экспериментальное время')
    
    # Теоретические данные
    plt.plot(lengths, theoretical_times, 'r--', linewidth=2, label='Теоретическое время (1 млн/сек)')
    
    plt.xlabel('Длина пароля', fontsize=12)
    plt.ylabel('Время подбора', fontsize=12)
    plt.title('Зависимость времени подбора пароля от его длины\n(Русский алфавит, 66 символов)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.yscale('log')  # Логарифмическая шкала для лучшего отображения
    
    # Сохранение графика
    if not filename:
        filename = f"password_time_graph_{int(time.time())}.png"
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nГрафик сохранен в файл: {filename}")
    
    # Сохранение данных в файл
    data_filename = "password_time_data.txt"
    with open(data_filename, 'w', encoding='utf-8') as f:
        f.write("Длина\tЭксп_время_сек\tТеор_время_сек\tКомбинации\n")
        for length, exp_time, theor_time in zip(lengths, times, theoretical_times):
            f.write(f"{length}\t{exp_time}\t{theor_time}\t{len(RUSSIAN_ALPHABET) ** length}\n")
    
    print(f"Данные сохранены в файл: {data_filename}")

def print_recommendations():
    """Вывод рекомендаций по выбору пароля"""
    print("\n" + "="*70)
    print("РЕКОМЕНДАЦИИ ПО ВЫБОРУ ПАРОЛЯ")
    print("="*70)
    print("1. 💡 ДЛИНА ПАРОЛЯ:")
    print("   - Социальные сети: 8+ символов")
    print("   - Электронная почта: 10+ символов") 
    print("   - Банковские сервисы: 12+ символов")
    print("   - Критически важные данные: 14+ символов")
    print()
    print("2. 🔒 СЛОЖНОСТЬ ПАРОЛЯ:")
    print("   - Используйте буквы разного регистра")
    print("   - Добавляйте цифры и специальные символы (если система позволяет)")
    print("   - Избегайте словарных слов и личной информации")
    print()
    print("3. ⚡ ПРОИЗВОДИТЕЛЬНОСТЬ АТАКУЮЩЕГО:")
    print("   - Персональный компьютер: 10^6 - 10^8 попыток/сек")
    print("   - GPU кластер: до 10^12 попыток/сек")
    print("   - Учитывайте рост вычислительной мощности со временем")
    print()
    print("4. 🛡️  ДОПОЛНИТЕЛЬНЫЕ МЕРЫ:")
    print("   - Двухфакторная аутентификация (2FA)")
    print("   - Регулярная смена паролей (каждые 3-6 месяцев)")
    print("   - Использование менеджеров паролей")
    print("   - Уникальные пароли для каждого сервиса")
    print()
    print("5. 📊 ОЦЕНКА ВРЕМЕНИ ВЗЛОМА ДЛЯ РУССКОГО АЛФАВИТА (66 символов):")
    
    attempts_per_second = 1000000  # 1 млн попыток в секунду
    for length in [6, 8, 10, 12, 14]:
        theor_time, combinations = calculate_theoretical_time(length, attempts_per_second)
        print(f"   - {length} символов: {format_time(theor_time)} ({combinations:,} комбинаций)")

def quick_demo():
    """Быстрая демонстрация без реального подбора"""
    print("\n🚀 БЫСТРАЯ ДЕМОНСТРАЦИЯ ВРЕМЕНИ ПОДБОРА")
    print("="*50)
    print("Длина\tКомбинации\t\tВремя взлома (1 млн/сек)")
    print("-"*50)
    
    attempts_per_second = 1000000
    for length in range(4, 13, 2):
        theor_time, combinations = calculate_theoretical_time(length, attempts_per_second)
        print(f"{length}\t{combinations:>15,}\t{format_time(theor_time)}")

def main():
    random.seed(time.time())
    print("🔐 Анализ стойкости паролей на основе русского алфавита")
    print(f"📊 Размер алфавита: {len(RUSSIAN_ALPHABET)} символов")
    
    while True:
        print("\nВыберите действие:")
        print("1. 🎲 Генерация строки и анализ распределения символов")
        print("2. ⏱️  Измерение времени подбора пароля")
        print("3. 📈 Построение графика зависимости времени подбора от длины пароля")
        print("4. 💡 Рекомендации по выбору пароля")
        print("5. 🚀 Быстрая демонстрация")
        print("0. ❌ Выход")
        
        try:
            choice = int(input("Ваш выбор: "))
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите число.")
            continue
        
        if choice == 1:
            try:
                length = int(input("Введите длину строки: "))
                if length <= 0:
                    print("Длина должна быть положительным числом.")
                    continue
                if length > 1000:
                    print("Слишком большая длина. Максимум 1000 символов.")
                    continue
                
                random_str = generate_string(length)
                print(f"\nСгенерированная строка: {random_str}")
                analyze_distribution(random_str)
            except ValueError:
                print("Неверный ввод. Пожалуйста, введите число.")
        
        elif choice == 2:
            password = input("Введите пароль для анализа: ").strip()
            if not password:
                print("Пароль не может быть пустым.")
                continue
            if not all(c in RUSSIAN_ALPHABET for c in password):
                print("Пароль должен содержать только русские буквы.")
                continue
            if len(password) > 6:
                print("⚠️  Предупреждение: подбор длинных паролей может занять много времени!")
            
            print(f"\n🔍 Анализ пароля: {password}")
            print(f"📏 Длина: {len(password)} символов")
            
            avg_time = measure_crack_time(password)
            print(f"⏱️  Среднее время подбора: {format_time(avg_time)}")
            
            # Теоретическая оценка
            theor_time, combinations = calculate_theoretical_time(len(password))
            print(f"📊 Теоретическое время (1 млн/сек): {format_time(theor_time)}")
            print(f"🎲 Количество комбинаций: {combinations:,}")
        
        elif choice == 3:
            try:
                max_length = int(input("Введите максимальную длину пароля для анализа (2-5): "))
                if max_length < 2 or max_length > 6:
                    print("Рекомендуется длина от 2 до 5 символов.")
                    continue
                
                filename = input("Введите имя файла для графика (или Enter для автоимени): ").strip()
                filename = filename if filename else None
                generate_time_graph(max_length, filename)
            except ValueError:
                print("Неверный ввод. Пожалуйста, введите число.")
        
        elif choice == 4:
            print_recommendations()
        
        elif choice == 5:
            quick_demo()
        
        elif choice == 0:
            print("Выход из программы...")
            break
        
        else:
            print("Неверный выбор. Пожалуйста, выберите действие из списка.")

if __name__ == "__main__":
    try:
        plt.figure()
        plt.close()
    except:
        print("⚠️  Внимание: графический интерфейс не доступен. Графики будут сохраняться в файлы.")
    
    main()