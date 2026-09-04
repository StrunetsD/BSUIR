import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import re
import os
from sklearn.model_selection import train_test_split
from collections import Counter
import pickle


class TextDataset(Dataset):
    """Датасет для текстовых данных"""

    def __init__(self, texts, labels, vocab, max_length=500):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        # Преобразуем текст в последовательность индексов
        text_indices = self.text_to_indices(text)

        return {
            'text': torch.tensor(text_indices, dtype=torch.long),
            'label': torch.tensor(label, dtype=torch.long),
            'length': torch.tensor(len(text_indices), dtype=torch.long)
        }

    def text_to_indices(self, text):
        """Преобразование текста в последовательность индексов"""
        # Очищаем текст и приводим к нижнему регистру
        text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', '', text.lower())

        # Ограничиваем длину текста
        text = text[:self.max_length]

        # Создаем последовательность индексов
        indices = []
        for char in text:
            if char in self.vocab:
                indices.append(self.vocab[char])
            else:
                indices.append(self.vocab['<UNK>'])  # Неизвестный символ

        # Дополняем до максимальной длины
        if len(indices) < self.max_length:
            indices.extend([self.vocab['<PAD>']] * (self.max_length - len(indices)))

        return indices[:self.max_length]


class LanguageClassifier(nn.Module):
    """Нейросетевая модель для классификации языка"""

    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=256,
                 num_layers=2, num_classes=2, dropout=0.3):
        super(LanguageClassifier, self).__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers,
                            batch_first=True, bidirectional=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_dim * 2, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x, lengths=None):
        # Embedding
        x = self.embedding(x)

        # LSTM
        lstm_out, (hidden, _) = self.lstm(x)

        # Берем последний скрытый状态 от обоих направлений
        hidden = torch.cat((hidden[-2], hidden[-1]), dim=1)

        # Полносвязные слои
        x = self.dropout(hidden)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)

        return x


class NeuralLanguageDetector:
    """Нейросетевой детектор языка с упрощенным интерфейсом"""

    def __init__(self, model_path=None, vocab_path=None, max_length=500):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.max_length = max_length
        self.vocab = None
        self.model = None
        self.label_map = {0: 'eng', 1: 'ru'}  # 0 - английский, 1 - русский

        if model_path and vocab_path:
            self.load_model(model_path, vocab_path)

    def build_vocab(self, texts, min_freq=5):
        """Построение словаря из текстов"""
        # Собираем все символы
        all_chars = []
        for text in texts:
            cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', '', text.lower())
            all_chars.extend(list(cleaned_text))

        # Считаем частоты
        char_freq = Counter(all_chars)

        # Создаем словарь
        vocab = {'<PAD>': 0, '<UNK>': 1}
        idx = 2

        for char, freq in char_freq.items():
            if freq >= min_freq:
                vocab[char] = idx
                idx += 1

        print(f"Создан словарь размером: {len(vocab)}")
        return vocab

    def prepare_data(self, english_texts, russian_texts, test_size=0.2):
        """Подготовка данных для обучения"""
        # Создаем метки
        texts = english_texts + russian_texts
        labels = [0] * len(english_texts) + [1] * len(russian_texts)  # 0 - eng, 1 - ru

        # Строим словарь
        self.vocab = self.build_vocab(texts)

        # Разделяем на train/test
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )

        return X_train, X_test, y_train, y_test

    def train(self, english_texts, russian_texts, epochs=10, batch_size=32,
              learning_rate=0.001, model_save_path='neural_model.pth',
              vocab_save_path='vocab.pkl'):
        """Обучение модели"""

        # Подготавливаем данные
        X_train, X_test, y_train, y_test = self.prepare_data(english_texts, russian_texts)

        # Создаем датасеты и даталодеры
        train_dataset = TextDataset(X_train, y_train, self.vocab, self.max_length)
        test_dataset = TextDataset(X_test, y_test, self.vocab, self.max_length)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

        # Инициализируем модель
        self.model = LanguageClassifier(
            vocab_size=len(self.vocab),
            embedding_dim=128,
            hidden_dim=256,
            num_layers=2,
            num_classes=2
        ).to(self.device)

        # Оптимизатор и функция потерь
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-5)
        criterion = nn.CrossEntropyLoss()

        # Обучение
        train_losses = []
        test_accuracies = []

        print("Начинаем обучение нейросетевой модели...")

        for epoch in range(epochs):
            # Режим обучения
            self.model.train()
            total_loss = 0

            for batch in train_loader:
                texts = batch['text'].to(self.device)
                labels = batch['label'].to(self.device)

                optimizer.zero_grad()
                outputs = self.model(texts)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            # Валидация
            self.model.eval()
            correct = 0
            total = 0

            with torch.no_grad():
                for batch in test_loader:
                    texts = batch['text'].to(self.device)
                    labels = batch['label'].to(self.device)

                    outputs = self.model(texts)
                    _, predicted = torch.max(outputs.data, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()

            accuracy = 100 * correct / total
            avg_loss = total_loss / len(train_loader)

            train_losses.append(avg_loss)
            test_accuracies.append(accuracy)

            print(f'Epoch [{epoch + 1}/{epochs}], Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%')

        # Сохраняем модель и словарь
        self.save_model(model_save_path, vocab_save_path)
        print(f"Модель сохранена: {model_save_path}")
        print(f"Словарь сохранен: {vocab_save_path}")

        return train_losses, test_accuracies

    def detect(self, text):
        """Определение языка для одного текста"""
        if self.model is None or self.vocab is None:
            raise ValueError("Модель не загружена. Сначала обучите или загрузите модель.")

        self.model.eval()

        # Преобразуем текст в тензор
        dataset = TextDataset([text], [0], self.vocab, self.max_length)
        text_tensor = dataset[0]['text'].unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(text_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(outputs, dim=1).item()
            confidence = probabilities[0][predicted_class].item()

        language = self.label_map[predicted_class]

        results ={
            "language": language,
            "confidence": confidence
        }

        return results

    def detect_batch(self, texts):
        """Определение языка для списка текстов"""
        results = []
        for text in texts:
            lang, conf = self.detect(text)
            results.append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'language': lang,
                'confidence': conf
            })
        return results

    def save_model(self, model_path, vocab_path):
        """Сохранение модели и словаря"""
        if self.model and self.vocab:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'model_config': {
                    'vocab_size': len(self.vocab),
                    'embedding_dim': 128,
                    'hidden_dim': 256,
                    'num_layers': 2,
                    'num_classes': 2
                }
            }, model_path)

            with open(vocab_path, 'wb') as f:
                pickle.dump(self.vocab, f)

    def load_model(self, model_path, vocab_path):
        """Загрузка модели и словаря"""
        # Загружаем словарь
        with open(vocab_path, 'rb') as f:
            self.vocab = pickle.load(f)

        # Загружаем модель
        checkpoint = torch.load(model_path, map_location=self.device)
        model_config = checkpoint['model_config']

        self.model = LanguageClassifier(**model_config).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])

        print(f"Модель загружена из {model_path}")
        print(f"Словарь загружен из {vocab_path}")
        print(f"Размер словаря: {len(self.vocab)}")


def load_texts_from_folder(folder_path, encoding='utf-8', min_text_length=50):
    """
    Загрузка текстов из папки с txt файлами

    Args:
        folder_path: путь к папке с текстовыми файлами
        encoding: кодировка файлов
        min_text_length: минимальная длина текста для включения в обучение

    Returns:
        list: список текстов
    """
    texts = []
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует")
        return texts

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read().strip()
                    if len(text) >= min_text_length:
                        texts.append(text)
                print(f"Загружен файл: {filename} ({len(text)} символов)")
            except UnicodeDecodeError:
                print(f"Ошибка кодировки в файле {filename}, пробуем другую кодировку...")
                try:
                    with open(file_path, 'r', encoding='windows-1251' if encoding == 'utf-8' else 'utf-8') as f:
                        text = f.read().strip()
                        if len(text) >= min_text_length:
                            texts.append(text)
                    print(f"Загружен файл: {filename} с альтернативной кодировкой ({len(text)} символов)")
                except Exception as e:
                    print(f"Не удалось загрузить {filename}: {e}")
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")

    print(f"Загружено текстов из {folder_path}: {len(texts)}")
    return texts


# ==================== УПРОЩЕННЫЙ ИНТЕРФЕЙС ДЛЯ ВНЕШНЕГО ИСПОЛЬЗОВАНИЯ ====================

def train_model(english_folder, russian_folder, model_path='neural_model.pth',
                vocab_path='vocab.pkl', epochs=10, batch_size=32, learning_rate=0.001,
                max_texts_per_language=5000, min_text_length=50):
    """
    Обучение модели детектора языка на текстовых файлах из папок

    Args:
        english_folder: путь к папке с английскими текстовыми файлами (utf-8)
        russian_folder: путь к папке с русскими текстовыми файлами (windows-1251)
        model_path: путь для сохранения модели
        vocab_path: путь для сохранения словаря
        epochs: количество эпох обучения
        batch_size: размер батча
        learning_rate: скорость обучения
        max_texts_per_language: максимальное количество текстов для каждого языка
        min_text_length: минимальная длина текста

    Returns:
        NeuralLanguageDetector: обученный детектор
    """
    print("Загрузка английских текстов...")
    english_texts = load_texts_from_folder(
        english_folder,
        encoding='utf-8',
        min_text_length=min_text_length
    )

    print("Загрузка русских текстов...")
    russian_texts = load_texts_from_folder(
        russian_folder,
        encoding='windows-1251',
        min_text_length=min_text_length
    )

    # Ограничиваем количество текстов
    english_texts = english_texts[:max_texts_per_language]
    russian_texts = russian_texts[:max_texts_per_language]

    print(f"Всего английских текстов для обучения: {len(english_texts)}")
    print(f"Всего русских текстов для обучения: {len(russian_texts)}")

    if not english_texts or not russian_texts:
        raise ValueError("Недостаточно данных для обучения. Проверьте пути к папкам и файлы.")

    detector = NeuralLanguageDetector()
    detector.train(english_texts, russian_texts, epochs=epochs, batch_size=batch_size,
                   learning_rate=learning_rate, model_save_path=model_path,
                   vocab_save_path=vocab_path)
    return detector


def load_trained_model(model_path, vocab_path):
    """
    Загрузка предварительно обученной модели

    Args:
        model_path: путь к файлу модели
        vocab_path: путь к файлу словаря

    Returns:
        NeuralLanguageDetector: загруженный детектор
    """
    detector = NeuralLanguageDetector()
    detector.load_model(model_path, vocab_path)
    return detector


def detect_language(detector, text):
    """
    Определение языка текста

    Args:
        detector: обученный детектор языка
        text: текст для анализа (уже очищенный)

    Returns:
        tuple: (язык, уверенность)
    """
    return detector.detect(text)


def detect_language_batch(detector, texts):
    """
    Определение языка для списка текстов

    Args:
        detector: обученный детектор языка
        texts: список текстов для анализа

    Returns:
        list: список результатов с языком и уверенностью для каждого текста
    """
    return detector.detect_batch(texts)


# ==================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ====================

def example_usage():
    """Пример использования упрощенного интерфейса"""

    # Пути к папкам с данными
    english_folder = 'english_files'  # Папка с английскими txt файлами в UTF-8
    russian_folder = 'russian_files'  # Папка с русскими txt файлами в Windows-1251

    model_path = 'trained_model.pth'
    vocab_path = 'vocabulary.pkl'

    # Проверяем существование модели
    if os.path.exists(model_path) and os.path.exists(vocab_path):
        print("=== ЗАГРУЗКА СУЩЕСТВУЮЩЕЙ МОДЕЛИ ===")
        detector = load_trained_model(model_path, vocab_path)
    else:
        print("=== ОБУЧЕНИЕ НОВОЙ МОДЕЛИ ===")
        detector = train_model(
            english_folder=english_folder,
            russian_folder=russian_folder,
            model_path=model_path,
            vocab_path=vocab_path,
            epochs=10,
            max_texts_per_language=1000
        )

    # Тестирование
    test_texts = [
        "This is an English text to test the language detector.",
        "Это русский текст для проверки работы детектора языка.",
        "Hello world! How are you doing today?",
        "Привет мир! Как у вас дела сегодня?",
        "The quick brown fox jumps over the lazy dog.",
        "Съешь же ещё этих мягких французских булок, да выпей чаю."
    ]

    print("\n=== ТЕСТИРОВАНИЕ ===")
    for text in test_texts:
        language, confidence = detect_language(detector, text)
        print(f"Текст: {text[:50]}...")
        print(f"Язык: {language}, Уверенность: {confidence:.4f}\n")

    # Пакетное определение
    print("=== ПАКЕТНОЕ ОПРЕДЕЛЕНИЕ ===")
    batch_results = detect_language_batch(detector, test_texts)
    for result in batch_results:
        print(f"Текст: {result['text']}")
        print(f"Язык: {result['language']}, Уверенность: {result['confidence']:.4f}\n")


if __name__ == "__main__":
    example_usage()