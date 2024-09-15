#include <iostream>

int factorial(int n);
int factorial1(int n);


using namespace std;

int main()
{
	setlocale(LC_ALL, "rus");
	int n;
	cout << "Введите число для вычисления факториала: ";
	cin >> n;

	int res1 = factorial(n);
	int res2 = factorial1(n);

	cout << "Значение факториала с использованием рекурсивной функции: " << res1 << endl;
	cout << "Значение факториала с использованием цикла: " << res2 << endl;

	if (res1 == res2)
		cout << "Оба значения факториала совпадают." << endl;
	else
		cout << "Значения факториала различаются." << endl;

	return 0;
}

int factorial(int n)
{
	if (n < 0)
		return -1;
	if (n == 0)
		return 1;
	return n * factorial(n - 1);
}

int factorial1(int n)
{
	int res = 1;
	for (int i = 1; i <= n; i++)
	{
		res *= i;
	}
	return res;
}