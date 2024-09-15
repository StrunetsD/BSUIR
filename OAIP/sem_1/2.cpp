#include <iostream>
#include <cmath>
#include <Windows.h>


double F;
double x;
double y;
int maximum(double x, double y) { 
	if (x > y) 
		return x;
	return y;
	
}
int minimum(double x, double y) {
	if (x < y)
		return x;
	return y;
}
int main() {
	
	setlocale(LC_ALL, "Rus");
	double x;
	std::cout << "Введите число x " << std::endl;
	if (std::cin >> x) {
		std::cout << "x= " << x << std::endl;
	}
	else {
		std::cout << "error" << std::endl;
		return 0;
	double y;
	std::cout << "Введите число y" << std::endl;
	if (std::cin >> y) {
		std::cout << "y= " << y << std::endl;
	}
	else {
		std::cout << "error" << std::endl;
		return 0;	
	}
	if ((x > 0) and (y >= 0)) {
		std::cout << "F= " << maximum(x, y + sqrt(x)) << std::endl;
	}
	else if (x < 0) {
		std::cout << "F= " << minimum(x, y) + pow(sin(x), 2) - pow(cos(y), 2) << std::endl;
	}
	else {
		std::cout << "F= " << x / 2 + exp(y) << std::endl;
	}
}