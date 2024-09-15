#include <iostream>

const int MAX_LENGTH = 100; // Максимальная длина вводимой строки
void fun(char str[]) {
    bool isFirstChar = true; // Флаг для определения первого символа слова

    for (int i = 0; str[i] != '\0'; i++) {
        if (isFirstChar && std::isalpha(str[i])) {//isalpha проверяет является ли аргумент буквой
            str[i] = '?'; // Замена первой буквы на вопросительный знак
            isFirstChar = false; // Сброс флага после замены первой буквы
        }
        else if (std::isspace(str[i])) { //Функция std::isspace() возвращаетx true, если переданный ей символ является пробелом.
            isFirstChar = true; // Установка флага перед началом нового слова
        }
    }
}

int main() {
    setlocale(LC_ALL, "RUS");
    char str[MAX_LENGTH]; // Массив символов для хранения строки
    std::cout << "Введите строку: ";
    std::cin.getline(str, MAX_LENGTH); // Ввод строки с учетом пробелов

    fun(str); // Вызов функции для замены первой буквы каждого слова

    std::cout << "Результат: " << str << std::endl; // Вывод результата
}


