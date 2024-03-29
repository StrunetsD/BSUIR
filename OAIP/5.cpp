﻿#include <iostream>

int main() {
    setlocale(LC_ALL, "RUS"); // Установка локали для вывода сообщений на русском языке
    int n; // Переменная для размерности матрицы
    std::cout << "Введите размерность матрицы: "; // Вывод строки
    std::cin >> n; // Ввод значения размерности матрицы
    double proizv = 1; // Переменная для хранения произведения элементов матрицы
    int sum = 0; // Переменная для хранения суммы элементов матрицы
    int counter = 0; // Переменная для подсчета количества замененных элементов

    int** arr = new int* [n]; // Выделение памяти для двумерного массива размером n x n
    for (int i = 0; i < n; i++) {
        arr[i] = new int[n]; // Выделение памяти для каждой строки массива
    }

    std::cout << "Введите элементы матрицы:" << std::endl;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            while (true) {
                std::cout << "Элемент [" << i << "][" << j << "]: ";
                if (std::cin >> arr[i][j]) {
                    break; // Ввод является целым числом, выходим из цикла
                }
                else {
                    std::cout << "Ошибка ввода. Пожалуйста, введите целое число." << std::endl;
                    return 0;
                    
                }
            }
        }
    }

    // Замена элементов выше главной и побочной диагоналей на 1
    for (int i = 0; i < n / 2; i++) {
        for (int j = 1 + i; j < n - 1 - i; j++) {
            arr[i][j] = 1; // Замена элемента на 1
        }

        counter++; // Увеличение счетчика замененных элементов
    }

    // Вывод результатов
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            std::cout << arr[i][j] << '\t'; // Вывод элемента матрицы
        }
        std::cout << std::endl; // Переход на новую строку
    }
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            proizv *= arr[i][j]; // Вычисление произведения элементов матрицы
            sum += arr[i][j]; // Вычисление суммы элементов матрицы
        }
    }

    std::cout << "proizv= " << proizv << std::endl; // Вывод значения произведения
    std::cout << "sum= " << sum - counter << std::endl; // Вывод значения суммы за вычетом замененных элементов

    // Освобождение памяти
    for (int i = 0; i < n; i++) {
        delete[] arr[i]; // Освобождение памяти для каждой строки массива
    }
    delete[] arr; // Освобождение памяти для массива

    return 0; // Возвращение значения 0, указывающего на успешное завершение программы
}