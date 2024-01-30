#include <iostream>
#include <fstream>

using namespace std;

int main()
{
	setlocale(LC_ALL, "rus");
	char* inputPath = new char[256];
	cout << "Введите файл для чтения: ";
	cin.getline(inputPath, 256);

	char* outputPath = new char[256];
	cout << "Введите файл для вывода: ";
	cin.getline(outputPath, 256);

	ifstream fIn(inputPath);// поток чтения из файла
	if (!fIn.is_open())
		return -1;

	ofstream fOut(outputPath, false);// поток ввода в файл ( false - очистка файла при вводе)
	if (!fOut.is_open())
		return -2;

	int counter = 0;// ищет каждый второй символ


	while (!fIn.eof())// eof - проверка конца файла 
	{
		char ch = fIn.get(); // get - читает посимвольно 
		char* buf = new char;
		buf[0] = ch;

		if (counter == 1)
		{
			buf[0] = '1';
			fOut.write(buf, 1);// write - записывает в файл вывода
			counter = 0;
			delete[] buf;
			continue;

		}
		fOut.write(buf, 1);
		counter++;
		delete[] buf;
	}

	fIn.close();
	fOut.close();
	delete[]inputPath;
	delete[]outputPath;
	system("pause");
}