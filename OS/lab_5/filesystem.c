#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_NAME 256       // Максимальная длина имени файла или директории
#define MAX_FILES 100      // Максимальное количество файлов и поддиректорий в директории
#define MAX_CONTENT 10240  // Максимальный размер содержимого файла
#define BLOCK_SIZE 128     // Размер блока для хранения файла

// Структура для представления файла
typedef struct File {
    char name[MAX_NAME];               // Имя файла
    char content[MAX_CONTENT];         // Содержимое файла
    int indexes[MAX_CONTENT / BLOCK_SIZE]; // Индексы блоков
    int size;                          // Размер файла
} File;

// Структура для представления директории
typedef struct Directory {
    char name[MAX_NAME];               // Имя директории
    struct Directory *parent;          // Указатель на родительскую директорию
    struct Directory *subdirs[MAX_FILES]; // Поддиректории
    int subdir_count;                  // Количество поддиректорий
    File *files[MAX_FILES];            // Файлы в директории
    int file_count;                    // Количество файлов
} Directory;

// Функция для создания новой директории
Directory *create_directory(Directory *parent, const char *name) {
    Directory *dir = (Directory *)malloc(sizeof(Directory)); // Выделение памяти для директории
    strcpy(dir->name, name);    // Копирование имени директории
    dir->parent = parent;       // Установка родительской директории
    dir->subdir_count = 0;      // Инициализация счетчика поддиректорий
    dir->file_count = 0;        // Инициализация счетчика файлов
    if (parent) {
        parent->subdirs[parent->subdir_count++] = dir; // Добавление директории в родительскую
    }
    return dir;
}

// Функция для создания нового файла в директории
File *create_file(Directory *dir, const char *name) {
    File *file = (File *)malloc(sizeof(File)); // Выделение памяти для файла
    strcpy(file->name, name);    // Копирование имени файла
    file->size = 0;              // Инициализация размера файла
    memset(file->indexes, -1, sizeof(file->indexes)); // Инициализация индексов блоков
    dir->files[dir->file_count++] = file; // Добавление файла в директорию
    return file;
}

// Функция для записи содержимого в файл
void write_to_file(File *file, const char *content) {
    int content_len = strlen(content); // Длина содержимого
    file->size = content_len;          // Установка размера файла
    strncpy(file->content, content, MAX_CONTENT); // Копирование содержимого

    // Определение количества блоков для хранения содержимого
    int block_count = (content_len + BLOCK_SIZE - 1) / BLOCK_SIZE;
    for (int i = 0; i < block_count; i++) {
        file->indexes[i] = i; // Установка индексов блоков
    }
}

// Функция для чтения содержимого файла
void read_file(File *file) {
    printf("Содержимое файла %s: ", file->name);

    int block_count = (file->size + BLOCK_SIZE - 1) / BLOCK_SIZE; // Количество блоков
    for (int i = 0; i < block_count; i++) {
        int start = i * BLOCK_SIZE; // Начало блока
        int end = start + BLOCK_SIZE; // Конец блока
        if (end > file->size) end = file->size; // Корректировка конца блока
        printf("%.*s", end - start, file->content + start); // Вывод блока
    }
    printf("\n");
}

// Функция для отображения файловой системы
void dump_filesystem(Directory *dir, int depth) {
    for (int i = 0; i < depth; i++) printf("  "); // Отступы для визуализации
    printf("Директория: %s\n", dir->name); // Вывод имени директории

    // Вывод файлов в директории
    for (int i = 0; i < dir->file_count; i++) {
        File *file = dir->files[i];
        for (int j = 0; j < depth + 1; j++) printf("  "); // Отступы
        printf("Файл: %s (размер: %d, блоки: ", file->name, file->size);

        // Вывод индексов блоков
        int block_count = (file->size + BLOCK_SIZE - 1) / BLOCK_SIZE;
        for (int k = 0; k < block_count; k++) {
            printf("%d ", file->indexes[k]);
        }
        printf(")\n");
    }

    // Рекурсивный вызов для поддиректорий
    for (int i = 0; i < dir->subdir_count; i++) {
        dump_filesystem(dir->subdirs[i], depth + 1);
    }
}

// Функция для импорта директории из реальной файловой системы
void import_directory(Directory *virtual_dir, const char *real_path) {
    struct dirent *entry;
    struct stat statbuf;
    char full_path[MAX_NAME];

    DIR *dp = opendir(real_path); // Открытие реальной директории
    if (!dp) {
        perror("Ошибка открытия директории");
        return;
    }

    // Чтение содержимого директории
    while ((entry = readdir(dp)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue; // Пропуск специальных записей
        }

        snprintf(full_path, sizeof(full_path), "%s/%s", real_path, entry->d_name); // Полный путь
        if (stat(full_path, &statbuf) == -1) {
            perror("Ошибка получения информации о файле");
            continue;
        }

        // Если это директория, рекурсивно импортируем её содержимое
        if (S_ISDIR(statbuf.st_mode)) {
            Directory *subdir = create_directory(virtual_dir, entry->d_name);
            import_directory(subdir, full_path);
        } 
        // Если это файл, создаем файл в виртуальной директории
        else if (S_ISREG(statbuf.st_mode)) {
            File *file = create_file(virtual_dir, entry->d_name);

            FILE *fp = fopen(full_path, "r"); // Открытие файла для чтения
            if (fp) {
                fread(file->content, 1, MAX_CONTENT, fp); // Чтение содержимого файла
                file->size = strlen(file->content); // Установка размера файла

                // Определение количества блоков для хранения содержимого
                int block_count = (file->size + BLOCK_SIZE - 1) / BLOCK_SIZE;
                for (int i = 0; i < block_count; i++) {
                    file->indexes[i] = i; // Установка индексов блоков
                }
                fclose(fp); // Закрытие файла
            } else {
                perror("Ошибка чтения файла");
            }
        }
    }
    closedir(dp); // Закрытие директории
}

int main() {
    Directory *root = create_directory(NULL, "/"); // Создание корневой директории

    printf("Импортируем файловую систему...\n");
    import_directory(root, "."); // Импортирование файловой системы из текущей директории

    printf("\nФайловая система:\n");
    dump_filesystem(root, 0); // Вывод структуры файловой системы


}