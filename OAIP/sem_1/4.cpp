﻿#include <iostream>

using namespace std;

void sorting(int arr[], int n) { // Функция для сортировки массива в порядке убывания
    for (int i = 0; i < n - 1; i++) { // Внешний цикл для прохода по всем элементам массива
        for (int j = 0; j < n - i - 1; j++) { // Внутренний цикл для сравнения и обмена соседних элементов
            if (arr[j] < arr[j + 1]) { // Если текущий элемент меньше следующего элемента
                int buff = arr[j]; // Временная переменная для хранения текущего элемента
                arr[j] = arr[j + 1]; // Замена текущего элемента на следующий элемент
                arr[j + 1] = buff; // Замена следующего элемента на временную переменную
            }
        }
    }
}

pair<int, int> function(int n) { // Функция для выполнения определенных операций на массиве
    int* arr = new int[n]; // Выделение памяти для массива размером n
    for (int i = 0; i < n; i++) { // Цикл для ввода элементов массива
        cin >> arr[i]; // Ввод элемента массива
    }

    sorting(arr, n); // Вызов функции для сортировки массива в порядке убывания

    int min_num = arr[0]; // Инициализация переменной для минимального числа
    int max_repeats = -1; // Инициализация переменной для максимального количества повторений
    int cur_num = arr[0]; // Инициализация переменной для текущего числа
    int repeats = 1; // Инициализация переменной для количества повторений текущего числа

    for (int i = 1; i < n; i++) { // Цикл для поиска наиболее часто повторяющегося элемента
        if (cur_num == arr[i]) { // Если текущий элемент равен следующему элементу
            repeats++; // Увеличение счетчика повторений
        }
        else {
            if (repeats > max_repeats) { // Если количество повторений текущего числа больше максимального количества повторений
                max_repeats = repeats; // Обновление максимального количества повторений
                min_num = cur_num; // Обновление минимального числа
            }
            else if (repeats == max_repeats) { // Если количество повторений текущего числа равно максимальному количеству повторений
                min_num = min(min_num, cur_num); // Обновление минимального числа (выбор наименьшего из двух чисел)
            }

            cur_num = arr[i]; // Обновление текущего числа
            repeats = 1; // Сброс счетчика повторений
        }
    }

    if (repeats > max_repeats) { // Проверка повторений для последнего элемента
        max_repeats = repeats; // Обновление максимального количества повторений
        min_num = cur_num; // Обновление минимального числа
    }
    else if (repeats == max_repeats) { // Если количество повторений последнего числа равно максимальному количеству повторений
        min_num = min(min_num, cur_num); // Обновление минимального числа (выбор наименьшего из двух чисел)
    }

    delete[] arr; // Освобождение памяти, выделенной для массива
    return make_pair(min_num, max_repeats); // Возврат пары значений
}

int main() {
    int n;
    cout << "Enter n: "; // Вывод строки
    cin >> n; // размер массива 
    pair<int, int> result = function(n);   
    cout << "Minimum number: " << result.first << endl; // Вывод значения минимального числа
    cout << "Number of repeats: " << result.second << endl; // Вывод значения количества повторений
}