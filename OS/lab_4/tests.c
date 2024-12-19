#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "lab44.h"
// Функция для тестирования инициализации FileManager
void test_initialization() {
struct FileManager file;
file.index_of_memory = 0;
file.data_index = 0;
memset(file.data, 0, sizeof(file.data));
file.head = NULL;
assert(file.index_of_memory == 0);
assert(file.data_index == 0);
assert(file.head == NULL);
}
// Функция для тестирования добавления блока
void test_add_block() {
struct FileManager file;
file.index_of_memory = 0;
file.head = NULL;
char id1[5] = {'A', 'B', 'C', 'D', '1'};
Add_Block(&file, 10, id1);
assert(file.index_of_memory == 15); // Длина блока + размер ID
assert(file.head != NULL);
assert(strncmp(file.head->idtf, id1, 5) == 0);
assert(file.head->length == 10);
}
// Функция для тестирования записи и чтения данных
void test_write_read_data() {
struct FileManager file;
file.index_of_memory = 0;
file.data_index = 0;
// memset(file.data, 0, sizeof(file.data));
file.head = NULL;char id1[5] = {'A', 'B', 'C', 'D', '1'};
Add_Block(&file, 10, id1);
const char *write_data = "Hello";
Write_Data(&file, write_data, id1);
// Проверка, что данные записаны правильно
assert(file.data[0] == 'A'); // ID блока
assert(file.data[1] == 'B');
assert(file.data[2] == 'C');
assert(file.data[3] == 'D');
assert(file.data[4] == '1');
assert(file.data[5] == 'H');
assert(file.data[6] == 'e');
assert(file.data[7] == 'l');
assert(file.data[8] == 'l');
assert(file.data[9] == 'o');
}
// Функция для тестирования удаления блока
void test_delete_block() {
struct FileManager file;
file.index_of_memory = 0;
file.head = NULL;
char id1[5] = {'A', 'B', 'C', 'D', '1'};
Add_Block(&file, 10, id1);
Del_Block(&file, &file.head, id1);
assert(file.head == NULL); // Блок должен быть удален
}
// Функция для тестирования компактации данных
void test_compact_data() {
struct FileManager file;
file.index_of_memory = 0;
file.data_index = 0;
//memset(file.data, 0, sizeof(file.data));
file.head = NULL;
char id1[5] = {'A', 'B', 'C', 'D', '1'};
Add_Block(&file, 5, id1);
Write_Data(&file, "Data", id1);char id2[5] = {'A', 'B', 'C', 'D', '2'};
Add_Block(&file, 3, id2);
Write_Data(&file, "New", id2);
Del_Block(&file, &file.head, id1);
compactData(&file);
// Проверка, что данные записаны
//printf(file.data[5], file.data[6], file.data[7]);
assert(file.data[5] == 'N');
assert(file.data[6] == 'e');
assert(file.data[7] == 'w');
}
// Функция для выполнения всех тестов
void run_tests() {
test_initialization();
test_add_block();
test_write_read_data();
test_delete_block();
test_compact_data();
printf("Все тесты пройдены!\n");
}
int main() {
run_tests();
return 0;
}