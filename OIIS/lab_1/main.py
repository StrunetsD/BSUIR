import numpy as np
import matplotlib.pyplot as plt

def generate_signal(function, frequency, length):
    t = np.linspace(0, 1, length, endpoint=False)
    if function == 'sin':
        signal = np.sin(2 * np.pi * frequency * t)
    elif function == 'cos':
        signal = np.cos(2 * np.pi * frequency * t)
    else:
        raise ValueError("Выберите либо 'sin', либо 'cos'")
    return signal

def my_fft(signal):
    x = signal
    N = len(x)
    
   
    if N <= 1:
        return x
    
    even = my_fft(x[0::2])
    odd = my_fft(x[1::2])
    
    T = [np.exp(-2j * np.pi * k / N) * odd[k] for k in range(N//2)]
    
    
    return np.concatenate([even + T, even - T])


function_type = 'sin'  # тип сигнала: 'sin' или 'cos'
frequency = 5         # частота сигнала (Гц)
signal_length = 64    # количество точек (должно быть степенью двойки для БПФ)


signal = generate_signal(function_type, frequency, signal_length)


my_fft_result = my_fft(signal)

np_fft_result = np.fft.fft(signal)


amplitude_spectrum_my = np.abs(my_fft_result)
amplitude_spectrum_np = np.abs(np_fft_result)




plt.figure(figsize=(10, 4))
plt.plot(signal)
plt.title('Исходный сигнал')
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.grid(True)
plt.savefig('signal_amplitude.png')  
plt.close() 


plt.figure(figsize=(10, 4))
freqs = np.fft.fftfreq(signal_length, 1/signal_length)
plt.stem(freqs[:signal_length//2], amplitude_spectrum_my[:signal_length//2])
plt.title('Амплитудный спектр сигнала (наша реализация БПФ)')
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда')
plt.grid(True)
plt.savefig('spectrum_amplitude_my.png')  
plt.close()  


plt.figure(figsize=(10, 4))
plt.stem(freqs[:signal_length//2], amplitude_spectrum_np[:signal_length//2])
plt.title('Амплитудный спектр сигнала (NumPy БПФ)')
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда')
plt.grid(True)
plt.savefig('spectrum_amplitude_np.png') 
plt.close() 

mse = np.mean((amplitude_spectrum_my - amplitude_spectrum_np)**2)
print(f"Среднеквадратичная ошибка между реализациями: {mse:.2e}")
