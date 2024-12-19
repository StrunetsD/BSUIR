#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lab44.h"

// Функция для компактизации данных в FileManager
void compactData(struct FileManager* file) {
    int writeIndex = 0;
    const int dataSize = sizeof(file->data) / sizeof(file->data[0]);

    // Проход по массиву данных и запись ненулевых значений
    for (int i = 0; i < dataSize; i++) {
        if (file->data[i] != '0') {
            file->data[writeIndex++] = file->data[i];
        }
    }

    // Заполнение оставшихся значений нулями
    for (int i = writeIndex; i < dataSize; i++) {
        file->data[i] = '\0';
    }

    // Обновление длины блоков в памяти
    struct block* temp = file->head;
    while (temp != NULL) {
        if (temp->have_data)
            temp->length = temp->data_length;
        temp = temp->next;
    }
    file->index_of_memory = writeIndex;  // Обновление индекса памяти
}

// Функция для добавления нового блока
void Add_Block(struct FileManager* file, int length, const char id[5]) {
    // Проверка на достаточное количество памяти
    if (100 - file->index_of_memory < length + 5) {
        printf("Нет столько памяти для выделения\n");
        return;
    }

    // Создание нового блока
    struct block* ptr = (struct block*)malloc(sizeof(struct block));
    ptr->length = length;  // Установка длины блока
    ptr->next = file->head;  // Добавление блока в начало списка
    file->head = ptr;

    // Копирование идентификатора блока
    for (int i = 0; i < 5; i++) {
        ptr->idtf[i] = id[i];
    }

    file->index_of_memory += (length + 5);  // Обновление индекса памяти
}

// Функция для просмотра блоков
void view(struct block* t) {
    while (t != NULL) {
        printf("Length: %d, ID: ", t->length);  // Вывод длины блока
        for (int i = 0; i < 5; i++) {
            printf("%c", t->idtf[i]);  // Вывод идентификатора блока
        }
        printf("\n");
        t = t->next;  // Переход к следующему блоку
    }
}

// Функция для записи данных в блок
void Write_Data(struct FileManager* file, const char write_data[], const char id[5]) {
    file->data_index = 0;
    int is_block = 0;
    struct block* temp = file->head;

    // Поиск блока с заданным идентификатором
    while (temp != NULL) {
        is_block = (strncmp(id, temp->idtf, 5) == 0);//которая сравнивает две строки (массивы символов) и проверяет, равны ли они в пределах определённого количества символов

        if (is_block) {
            // Проверка на переполнение блока
            if (temp->length < strlen(write_data)) {
                printf("Не хватит памяти, чтобы записать ваши данные в этот блок\n");
                return;
            }

            // Установка длины данных и отметка, что данные есть
            temp->data_length = strlen(write_data);
            temp->have_data = 1;

            // Заполнение данных нулями
            for (int i = file->data_index; i < file->data_index + temp->length + 5; i++) {
                file->data[i] = '0';
            }

            // Запись идентификатора блока
            for (int i = 0; i < 5; i++) {
                file->data[file->data_index + i] = temp->idtf[i];
            }

            file->data_index += 5;  // Обновление индекса данных

            // Запись данных в блок
            for (int i = 0; i < strlen(write_data); i++) {
                file->data[file->data_index + i] = write_data[i];
            }

            break;  // Завершение цикла
        }

        file->data_index += temp->length + 5;  // Переход к следующему блоку
        temp = temp->next;
    }
}

// Функция для чтения данных из блока
void Read_Data(struct FileManager* file, const char id[5]) {
    file->data_index = 0;
    int is_block = 0;
    struct block* temp = file->head;

    // Поиск блока с заданным идентификатором
    while (temp != NULL) {
        is_block = (strncmp(id, temp->idtf, 5) == 0);

        if (is_block) {
            // Проверка наличия данных
            if (!temp->have_data) {
                printf("Данных в блоке нет\n");
                return;
            }
            // Вывод данных из блока
            for (int i = file->data_index; i < file->data_index + temp->length + 5; i++) {
                printf("%c", file->data[i]);
            }
            printf("\n");
            break;  // Завершение цикла
        }

        file->data_index += (temp->length + 5);  // Переход к следующему блоку
        temp = temp->next;
    }
}

// Функция для удаления блока
void Del_Block(struct FileManager* file, struct block** top, const char id[5]) {
    file->data_index = 0;
    struct block* temp = NULL;
    struct block* current = *top;

    // Поиск блока с заданным идентификатором
    while (current != NULL) {
        int is_block = (strncmp(id, current->idtf, 5) == 0);//которая сравнивает две строки (массивы символов) и проверяет, равны ли они в пределах определённого количества символов

        if (is_block) {
            // Очистка данных блока
            for (int i = file->data_index; i < file->data_index + current->length + 5; i++) {
                file->data[i] = '0';
            }

            file->index_of_memory -= (current->length + 5);  // Обновление индекса памяти

            // Удаление блока из списка
            if (current == *top) {
                *top = current->next;
            } else {
                temp->next = current->next;
            }

            free(current);  // Освобождение памяти
            break;  // Завершение цикла
        }

        file->data_index += current->length + 5;  // Переход к следующему блоку
        temp = current;
        current = current->next;
    }
}

// Функция для удаления всех блоков
void del(struct block** top) {
    if (top == NULL || *top == NULL) {
        return;  // Проверка на пустой список
    }

    struct block* t;

    // Освобождение памяти для всех блоков
    while (*top != NULL) {
        t = *top;
        *top = (*top)->next;
        free(t);
    }
}