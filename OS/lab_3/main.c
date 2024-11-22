
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <semaphore.h>
#include <time.h>
#include <signal.h>

#define MAX_WAITING_CHAIRS 3

sem_t *barber_ready;
sem_t *customer_ready;
sem_t *queue_access;


typedef struct {
    int customers_waiting;
    int customer_numbers[MAX_WAITING_CHAIRS];
} BarberShop;

BarberShop *shop;

void barber() {
    while (1) {
        sem_wait(customer_ready);//захват доступа(получение сигнала)

        sem_wait(queue_access);
        if (shop->customers_waiting > 0) {
            int client_number = shop->customer_numbers[0];
            shop->customers_waiting--;

            for (int i = 0; i < shop->customers_waiting; i++) {
                shop->customer_numbers[i] = shop->customer_numbers[i + 1];
            }

            sem_post(queue_access);// освобождение доступа к очереди

            int haircut_time = rand() % 5 + 1;
            printf("Стрижка начата для клиента %d. Ожидающих клиентов: %d\n", client_number, shop->customers_waiting);

            sleep(haircut_time);

            printf("Клиент %d был пострижен\n", client_number);


            sem_wait(queue_access);
            if (shop->customers_waiting > 0) {
                sem_post(customer_ready);
            } else {
                printf("Парикмахер спит. Нет клиентов.\n");
            }
            sem_post(queue_access);
        } else {
            sem_post(queue_access);
            sem_wait(barber_ready);
        }
    }
}

void customer(int client_number) {
    sem_wait(queue_access);
    if (shop->customers_waiting < MAX_WAITING_CHAIRS) {
        shop->customer_numbers[shop->customers_waiting] = client_number;
        shop->customers_waiting++;
        printf("Клиент %d пришел. Ожидающих клиентов: %d\n", client_number, shop->customers_waiting);

        if (shop->customers_waiting == 1) {
            sem_post(barber_ready);
        }

        sem_post(queue_access);

        sem_post(customer_ready);

    } else {
        sem_post(queue_access);
        printf("Клиент %d ушел, нет места в приемной.\n", client_number);
    }
}

void signal_handler(int sig) {
    //закрытие семафоров
    sem_close(barber_ready);
    sem_close(customer_ready);
    sem_close(queue_access);
    //удаление семафоров
    sem_unlink("/barber_ready");
    sem_unlink("/customer_ready");
    sem_unlink("/queue_access");
    //освобождение памяти
    munmap(shop, sizeof(BarberShop));

    printf("Процесс завершен.\n");
    exit(0);
}

int main() {
    signal(SIGINT, signal_handler);
    //PROT_READ | PROT_WRITE указывает, что память может быть прочитана и записана.
    //MAP_SHARED | MAP_ANONYMOUS означает, что память будет совместно используемой и не будет связана с файлом.
    shop = (BarberShop *) mmap(NULL, sizeof(BarberShop), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (shop == MAP_FAILED) {
        perror("mmap failed");
        exit(1);
    }
    shop->customers_waiting = 0;

    barber_ready = sem_open("/barber_ready", O_CREAT, 0644, 0);
    customer_ready = sem_open("/customer_ready", O_CREAT, 0644, 0);
    queue_access = sem_open("/queue_access", O_CREAT, 0644, 1);

    if (barber_ready == SEM_FAILED || customer_ready == SEM_FAILED || queue_access == SEM_FAILED) {
        perror("sem_open failed");
        exit(1);
    }

    srand(time(NULL));

    pid_t barber_pid = fork();
    if (barber_pid == 0) {
        barber();
        exit(0);
    }

    for (int i = 0; i < 10; i++) {
        int arrival_interval = rand() % 3 + 1;
        sleep(arrival_interval);
        pid_t customer_pid = fork();
        if (customer_pid == 0) {
            customer(i + 1);
            exit(0);
        }
    }
    for (int i = 0; i < 10; i++) {
        wait(NULL);
    }

}









