#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lab44.h"

int main() {
    struct FileManager file;
    file.index_of_memory = 0;
    file.data_index = 0;
    memset(file.data, 0, sizeof(file.data));
    file.head = NULL;

    char ind1[5] = { 'A', 'B', 'C', 'D', '1' };
    char ind2[5] = { 'A', 'B', 'C', 'D', '2' };
    char ind3[5] = { 'A', 'B', 'C', 'D', '3' };
    char ind4[5] = { 'A', 'B', 'C', 'D', '4' };
    char ind5[5] = { 'A', 'B', 'C', 'D', '5' };
    char ind6[5] = { 'A', 'B', 'C', 'D', '6' };
    char ind7[5] = { 'A', 'B', 'C', 'D', '7' };

    Add_Block(&file, 1, ind1);
    Add_Block(&file, 5, ind2);
    Add_Block(&file, 7, ind3);
    Add_Block(&file, 4, ind4);
    Add_Block(&file, 10, ind5);
    Add_Block(&file, 10, ind6);
    Add_Block(&file, 90, ind7);

    printf("Содержимое списка:\n");
    view(file.head);

    printf("Значения data: ");
    for (int i = 0; i < 100; i++) {
        printf("%c", file.data[i]);
    }
    printf("\n");

    const char write_1[] = "Olaaa";
    Write_Data(&file, write_1, ind2);

    const char write_2[] = "BlaBla";
    Write_Data(&file, write_2, ind1);

    printf("Данные после записи:\n");
    Read_Data(&file, ind2);

    const char write_data[] = "Hello";
    Write_Data(&file, write_data, ind3);

    printf("Данные после записи:\n");
    Read_Data(&file, ind3);

    const char write_6[] = "Privet";
    Write_Data(&file, write_6, ind6);

    printf("Данные после записи:\n");
    Read_Data(&file, ind6);

    printf("Данные перед удаления блока:\n");
    for (int i = 0; i < 100; i++) {
        printf("%c", file.data[i]);
    }
    printf("\n\n");

    Del_Block(&file, &file.head, ind3);

    printf("Данные после удаления блока:\n");
    for (int i = 0; i < 100; i++) {
        printf("%c", file.data[i]);
    }
    printf("\n\n");

    compactData(&file);

    printf("Данные после операции перемещения:\n");
    for (int i = 0; i < 100; i++) {
        printf("%c", file.data[i]);
    }
    printf("\n\n");

    const char write_5[] = "Poka";
    Write_Data(&file, write_5, ind5);

    printf("Данные после записи:\n");
    Read_Data(&file, ind5);

    printf("Данные перед удаления блока:\n");
    for (int i = 0; i < 100; i++) {
        printf("%c", file.data[i]);
    }
    printf("\n\n");

    view(file.head);

    Read_Data(&file, ind6);
    del(&file.head);
    printf("После очистки:\n");
    view(file.head);

    return 0;
}
