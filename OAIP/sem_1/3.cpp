#include <cmath>
#include <iostream>
using namespace std;

const double e = 0.0001;

int factorial(int k) { // функция для вычесления факториала 
    if (k < 0)
        return 0;
    if (k == 0)
        return 1;
    else
        return k * factorial(k - 1);
}

double Y(double x) { 
    return (exp(x) - exp(x * (-1))) / 2; // функция для вычисления второго значения функции 
}

double S(double x)//функция для вычисления аппроксимации(замену одних математических объектов другими) функции
{
    double sum = 0,
    h = 0.00001, 
    y = 0;// sum  - текущая сумма ряда , h - шаг , с которым будет изменяться переменная x , y - сохранение точного значения функции 
    int k = 0;// считает кол-во итераций 
    while (fabs(sum - y) <= e)
    {   
        sum += pow(x, 2 * k + 1) / factorial(2 * k + 1);
        y = Y(x); // вычисляется значение функции Y(x) и сохраняется в y
        k++;
        cout << "Y(x) = " << y << "\tS(x) = " << sum << "\tRaznost = " << fabs(sum - y) << "\t" << x << endl;
        x += h;// x увеличивается на h ,чтобы перейти к сл. итерации 
    }
    int counter = k;// кол-во итераций 

    return counter;
}

int main()
{
    double x = 0;
    double res = S(x);
    cout << res;

}