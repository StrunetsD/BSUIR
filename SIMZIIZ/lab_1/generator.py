import random
import matplotlib.pyplot as plt

RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"

class LWVariant:
    ALL_RUSSIAN = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'

class PasswordGenerator:
    def __init__(self, lw_variant: str = LWVariant.ALL_RUSSIAN):
        if lw_variant is not None:
            self.charset = list(lw_variant)
        else:
            self.charset = list(LWVariant.ALL_RUSSIAN)

    def generate(self, length: int):
        return ''.join(random.choice(self.charset) for _ in range(length))
    
class FrequencyPlotter:
    def __init__(self, password_generator):
        self.password_generator = password_generator

    def plot_frequency(self, password_length: int, num_samples: int):
        frequencies = {symbol: 0 for symbol in self.password_generator.charset}
        
        for _ in range(num_samples):
            password = self.password_generator.generate(password_length)
            for symbol in password:
                frequencies[symbol] += 1
        symbols = list(frequencies.keys())
        counts = list(frequencies.values())

        plt.figure(figsize=(12, 6))
        plt.bar(symbols, counts)
        plt.xlabel('Символ')
        plt.ylabel('Частота')
        plt.title(f'Частота символов в {num_samples} паролях длиной {password_length}')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig('frequency_plot.png')

if __name__ == "__main__":
    generator = PasswordGenerator(lw_variant=LWVariant.ALL_RUSSIAN)
    plotter = FrequencyPlotter(generator)

    plotter.plot_frequency(password_length=16, num_samples=1000)