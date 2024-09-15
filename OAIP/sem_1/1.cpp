#include <iostream>
#include <cmath>
#include <Windows.h>


int main() {
	SetConsoleCP(1251);//кодировка для кириллицы 
	SetConsoleOutputCP(1251);
	std::cout << "Введите число a" << std::endl;
	double a; 
	if (std::cin >> a) {
		std::cout << "a= " << a << std::endl;
			}
	else {
		std::cout << "error" << std::endl;
		return -1;// остановка
	}
	
	std::cout << "Введите число b" << std::endl;
	double b;
	if (std::cin >> b) {
		std::cout << "b= " << b << std::endl;
	}
	else {
		std::cout << "error" << std::endl;
		return -2;// остановка 
	}
	double z1 = ((a - 1) * sqrt(a) - (b - 1) * sqrt(b)) / ((sqrt(pow(a, 3) * b)) + a * b + a * a - a);
	double z2 = (sqrt(a) - sqrt(b)) / a;
	std::cout << z1 << std::endl;
	std::cout << z2 << std::endl;
}