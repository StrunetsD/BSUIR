#include <iostream>
#include <fstream>
#include <string>

using namespace std;

struct Applicant {
    string name;
    int marks[4];
    double average;
};

const int MAX_APPLICANTS = 100;

void createDataFile(const string& filename) {
    ofstream file(filename);

    if (file.is_open()) {
        file.close();
        cout << "Файл успешно создан." << endl;
    }
    else {
        cout << "Ошибка создания файла." << endl;
    }
}

void viewData(const string& filename) {
    ifstream file(filename);

    if (file.is_open()) {
        string line;
        while (getline(file, line)) {
            cout << line << endl;
        }
        file.close();
    }
    else {
        cout << "Ошибка открытия файла для чтения." << endl;
    }
}

void addData(const string& filename, const string& data) {
    ofstream file(filename, ios::app); // Открываем файл в режиме добавления данных

    if (file.is_open()) {
        file << data << endl;
        file.close();
    }
    else {
        cout << "Ошибка открытия файла для записи." << endl;
    }
}

void calculateAverage(Applicant applicants[], int numApplicants) {
    for (int i = 0; i < numApplicants; i++) {
        int sum = 0;
        for (int j = 0; j < 4; j++) {
            sum += applicants[i].marks[j];
        }
        applicants[i].average = static_cast<double>(sum) / 4.0;
    }
}

void quickSort(Applicant applicants[], int low, int high) {
    if (low < high) {
        int i = low;
        int j = high;
        int mid = (low + high) / 2;
        double pivot = applicants[mid].average;

        while (i <= j) {
            while (applicants[i].average > pivot)
                i++;
            while (applicants[j].average < pivot)
                j--;

            if (i <= j) {
                Applicant temp = applicants[i];
                applicants[i] = applicants[j];
                applicants[j] = temp;
                i++;
                j--;
            }
        }

        quickSort(applicants, low, j);
        quickSort(applicants, i, high);
    }
}

int binarySearch(Applicant applicants[], int low, int high, double targetAverage) {
    while (low <= high) {
        int mid = low + (high - low) / 2;

        if (applicants[mid].average == targetAverage) {
            return mid;
        }
        else if (applicants[mid].average < targetAverage) {
            low = mid + 1;
        }
        else {
            high = mid - 1;
        }
    }

    return -1;
}

int main() {
    setlocale(LC_ALL, "RUS");
    string filename = "data.txt";
    Applicant applicants[MAX_APPLICANTS];
    Applicant initialApplicants[MAX_APPLICANTS]; // Массив для хранения изначальных данных
    int numApplicants = 0;

    // Создание файла с данными
    createDataFile(filename);

    // Добавление данных в файл
    addData(filename, "Иванов,10,10,10,10");
    addData(filename, "Петров,8,8,8,8");
    addData(filename, "Сидоров,9,9,9,9" );

    // Чтение данных из файла
    ifstream file(filename);
    if (file.is_open()) {
        while (!file.eof()) {
            string line;
            getline(file, line);

            if (!line.empty()) {
                size_t pos = line.find(",");
                initialApplicants[numApplicants].name = line.substr(0, pos);
                string marksStr = line.substr(pos + 1);//подстрока с какой-то позицией 
                size_t markPos = 0;
                for (int i = 0; i < 4; i++) {
                    size_t commaPos = marksStr.find(",", markPos);
                    if (commaPos != string::npos) {
                        initialApplicants[numApplicants].marks[i] = stoi(marksStr.substr(markPos, commaPos - markPos));//stoi - strToInt
                        markPos = commaPos + 1;
                    }
                    else {
                        initialApplicants[numApplicants].marks[i] = stoi(marksStr.substr(markPos));
                    }
                }
                numApplicants++;
            }
        }
        file.close();
    }

    // Копирование изначальных данных в массив applicants
    for (int i = 0; i < numApplicants; i++) {
        applicants[i] = initialApplicants[i];
    }

    // Расчет среднего балла для каждого абитуриента
    calculateAverage(applicants, numApplicants);

    // Вывод изначальных данных
    cout << "Изначальные данные из файла:" << endl;
    for (int i = 0; i < numApplicants; i++) {
        cout << initialApplicants[i].name << ": ";
        for (int j = 0; j < 4; j++) {
            cout << initialApplicants[i].marks[j] << " ";
        }
        cout << endl;
    }
    cout << endl;

    // Сортировка абитуриентов по убыванию среднего балла
    quickSort(applicants, 0, numApplicants - 1);
    cout << "Отсортированные данные из файла:" << endl;
    for (int i = 0; i < numApplicants; i++) {
        string out = applicants[i].name + ": " + to_string(applicants[i].average);;
        cout <<out << endl;
        addData(filename, out);
    }
 
    // Вычисление среднего балла по университету
    double universitySum = 0.0;
    for (int i = 0; i < numApplicants; i++) {
        universitySum += applicants[i].average;
    }
    double universityAverage = universitySum / static_cast<double>(numApplicants);

    // Вывод списка абитуриентов с баллом выше среднего балла по университету
    cout << "Список абитуриентов с баллом выше среднего балла по университету (" << universityAverage << "):" << endl;
    for (int i = 0; i < numApplicants; i++) {
        if (applicants[i].average > universityAverage) {
            cout << applicants[i].name << ": " << applicants[i].average << endl;
        }
    }

    double targetAverage = 9.0;
    int low = 0;
    int high = numApplicants - 1;
    int index = binarySearch(applicants, low, high, targetAverage);

    if (index != -1) {
        cout << "Абитуриент с баллом " << targetAverage << " найден: " << applicants[index].name << endl;
    }
    else {
        cout << "Абитуриент с баллом " << targetAverage << " не найден." << endl;
    }
   
}