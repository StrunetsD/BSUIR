#ifndef FILE_MANAGER_H
#define FILE_MANAGER_H

struct block {
    char idtf[5];
    int length;
    int have_data;
    int data_length;
    struct block* next;
};

struct FileManager {
    int index_of_memory;//для перемещения
    int data_index;
    char data[100];//эмуляция оперативной памяти
    struct block* head;//стек блоков 
};

void compactData(struct FileManager* file);
void Add_Block(struct FileManager* file, int length, const char id[5]);
void view(struct block* t);
void Write_Data(struct FileManager* file, const char write_data[], const char id[5]);
void Read_Data(struct FileManager* file, const char id[5]);
void Del_Block(struct FileManager* file, struct block** top, const char id[5]);
void del(struct block** top);

#endif // FILE_MANAGER_H
