import itertools
import time
import matplotlib.pyplot as plt
from generator import PasswordGenerator, LWVariant

class BruteForceTimePlotter:
    def __init__(self, password_generator):
        self.password_generator = password_generator

    def estimate_brute_force_time(self, password_length: int, samples: int):
        charset = self.password_generator.charset
        charset_size = len(charset)
        
        total_time = 0
        successful_samples = 0
        
        for sample in range(samples):
            target_password = self.password_generator.generate(length=password_length)
            
            start_time = time.time()
            found = False
            
            for i, attempt in enumerate(itertools.product(charset, repeat=password_length)):
                attempt_str = ''.join(attempt)
                
                if attempt_str == target_password:
                    found = True
                    break
                    
                if i > 1000000 and password_length > 2:
                    break
            
            end_time = time.time()
            
            if found:
                elapsed = end_time - start_time
                total_time += elapsed
                successful_samples += 1
        
        if successful_samples > 0:
            return total_time / successful_samples
        else:
            return float('inf')

    def estimate_smart(self, password_length: int):
        charset_size = len(self.password_generator.charset)
        total_combinations = charset_size ** password_length
        
        attempts_per_second = 1000000
        seconds = total_combinations / attempts_per_second / 2
        
        time_units = [
            ("секунд", 60),
            ("минут", 60),
            ("часов", 24),
            ("дней", 30),
            ("месяцев", 12),
            ("лет", 1),
            ("веков", 100),
            ("тысячелетий", 1000)
        ]
        
        current_time = seconds
        unit_name = "секунд"
        
        for unit, divisor in time_units:
            if current_time < divisor:
                unit_name = unit
                break
            current_time /= divisor
        
        return current_time, unit_name, total_combinations

    def plot_average_time(self, max_password_length: int, samples: int):
        lengths = list(range(1, max_password_length + 1))
        average_times = []
        time_labels = []
        
        for length in lengths:
            if length <= 3:
                time_val = self.estimate_brute_force_time(length, min(samples, 3))
                average_times.append(time_val)
                time_labels.append(f"{time_val:.3f}с")
            else:
                est_time, unit, combinations = self.estimate_smart(length)
                average_times.append(est_time)
                time_labels.append(f"{est_time:.1f} {unit}")
        
        plt.figure(figsize=(12, 6))
        plt.plot(lengths, average_times, 'o-', linewidth=2, markersize=8)
        plt.yscale('log')
        plt.xlabel('Длина пароля')
        plt.ylabel('Оценочное время подбора')
        plt.title('Время подбора в зависимости от длины пароля')
        plt.grid(True, alpha=0.3)
        
        for i, (x, y, label) in enumerate(zip(lengths, average_times, time_labels)):
            plt.annotate(label, (x, y), xytext=(5, 5), textcoords='offset points')
        
        plt.tight_layout()
        plt.savefig('brute_force_times_rus.png', dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    generator = PasswordGenerator(lw_variant=LWVariant.ALL_RUSSIAN)
    plotter = BruteForceTimePlotter(generator)
    
    plotter.plot_average_time(max_password_length=5, samples=3)