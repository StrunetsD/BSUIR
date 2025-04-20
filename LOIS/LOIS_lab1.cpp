// Лабораторная работа №1 по дисциплине Логические Основы Интеллектуальных Систем
// Выполнена студентом группы 321701:Струнцом Дмитрием Петровичем
//
// 30.03.2025
//
//  Задание:
//  Проверить является ли строка формулой сокращенного языка логики высказываний
//
// Использованные источники:
// Справочная система по дисциплине ЛОИС
// Логические основы интеллектуальных систем. Практикум

#include <iostream>
#include <fcntl.h>
#include <cwctype>
#include <string>
#include <vector>

using namespace std;

void printResult(bool result);
bool isAllUpper(const wstring &strTest);
bool isAllLetters(const wstring &strTest);
bool isAllDigitsFromOneToNine(const char ch);
bool haveOneLetter(const wchar_t ch);
bool countOfBracketsIsEqual(const wstring &strTest);
bool isInvalidCharacters(const wstring &strTest);
bool isAtomicFormula(const wstring &strTest);
bool isUnaryFormula(const wstring &strTest);
bool isBinaryFormula(const wstring &strTest);
bool checkStrIsFormula(const wstring &strTest);
bool isBinaryOperator(const wchar_t ch);
bool isConstanta(const wchar_t ch);
bool isConstanta(const wstring &strTest);

wstring takeOperand(wstring *strTest);
void checkUser();
const vector<pair<wstring, bool>> BINARY_OPS = {
    {L"\\/", false}, {L"/\\", false}, {L"->", false}, {L"~", false}};

// Вывод результатов
void printResult(bool result)
{
    if (result)
        wcout << L"Данная строка является формулой сокращенного языка логики высказывний" << endl;
    else
        wcout << L"Данная строка НЕ является формулой сокращенного языка логики высказывний" << endl;
}

// Проверка является ли строка формулой сокращенного языка логики высказываний.
bool checkStrIsFormula(const wstring &strTest)
{
    if (strTest.empty())
        return false;
    if (isInvalidCharacters(strTest))
        return false;

    if (isConstanta(strTest))
        return true;

    if (isAtomicFormula(strTest))
        return true;
    if (isUnaryFormula(strTest))
        return true;
    if (isBinaryFormula(strTest))
        return true;

    return false;
}
// Проверка на заглавные буквы
bool isAllUpper(const wstring &strTest)
{
    for (wchar_t c : strTest)
    {
        if (!isBinaryOperator(c))
            if (isalpha(c) && !isupper(c))
                return false;
    }
    return true;
}

// Проверка на наличие только букв
bool isAllLetters(const wstring &strTest)
{
    for (wchar_t c : strTest)
    {
        if (!isBinaryOperator(c))
            if (!iswalpha(c))
                return false;
    }
    return true;
}

// Проверка на наличие только цифр от 1 до 9
bool isAllDigitsFromOneToNine(const char ch)
{
    if (ch < L'1' || ch > L'9')
        return false;
    else
        return true;
}

// Проверка на наличие хотя бы одной буквы
bool haveOneLetter(const wchar_t ch)
{
    if (iswalpha(ch) && isupper(ch))
        return true;
    else
        return false;
}

// Проверка на одинаковое количество ( и )
bool countOfBracketsIsEqual(const wstring &strTest)
{
    int leftBrackets = 0, rightBrackets = 0;
    for (wchar_t c : strTest)
    {
        if (c == '(')
            leftBrackets++;
        if (c == ')')
            rightBrackets++;
    }
    if (leftBrackets == rightBrackets)
        return true;
    else
        return false;
}

bool isInvalidCharacters(const wstring &strTest)
{
    for (wchar_t ch : strTest)
    {
        // Блокировка русских букв
        if ((ch >= L'А' && ch <= L'я') || ch == L'ё' || ch == L'Ё')
            return true;

        // Проверка остальных допустимых символов
        bool valid = iswupper(ch) ||
                     iswdigit(ch) ||
                     ch == L'(' || ch == L')' ||
                     ch == L'!';

        // Проверка бинарных операторов
        for (const auto &op : BINARY_OPS)
            if (op.first.find(ch) != wstring::npos)
                valid = true;

        if (!valid)
            return true;
    }
    return false;
}

// Проверка на бинарную связку
bool isBinaryOperator(const wchar_t ch)
{
    if (ch == L'\\/' || ch == L'/\\' || ch == L'~' || ch == L'->')
        return true;
    else
        return false;
}

// Проверка на константу
bool isConstanta(const wstring &strTest)
{
    return strTest == L"0" || strTest == L"1";
}

// Проверка атомарной формулы
bool isAtomicFormula(const wstring &strTest)
{
    if (strTest.size() != 1)
        return false;

    wchar_t c = strTest[0];
    return (c >= L'A' && c <= L'Z');
}

// Проверка унарной формулы
bool isUnaryFormula(const wstring &strTest)
{
    if (strTest.size() < 4)
        return false;
    if (strTest[0] != L'(' || strTest[1] != L'!' || strTest.back() != L')')
        return false;

    wstring inner = strTest.substr(2, strTest.size() - 3);
    return checkStrIsFormula(inner);
}

bool isBinaryFormula(const wstring &strTest)
{
    if (strTest.size() < 5)
        return false;
    if (strTest[0] != L'(' || strTest.back() != L')')
        return false;

    wstring inner = strTest.substr(1, strTest.size() - 2);
    for (size_t i = 0; i < inner.size(); ++i)
    {
        for (const auto &op : BINARY_OPS)
        {
            if (inner.substr(i, op.first.size()) == op.first)
            {
                wstring left = inner.substr(0, i);
                wstring right = inner.substr(i + op.first.size());
                return checkStrIsFormula(left) && checkStrIsFormula(right);
            }
        }
    }
    return false;
}

void checkUser()
{
    wcout << L"Проверь свои знания" << endl;
    wstring formulaCheck;
    bool check;
    wstring answer, choice;

    formulaCheck = L"(¬(A∧B))";
    answer = L"1";
    wcout << L"Является ли строка формулой сокращенного языка логики высказываний?" << endl;
    wcout << formulaCheck << endl;
    wcout << L"\t1. Да\n\t2. Нет" << endl;
    getline(wcin, choice);
    if (answer == choice)
        wcout << L"Верно." << endl;
    else
        wcout << L"Неверно." << endl;
    printResult(checkStrIsFormula(formulaCheck));

    formulaCheck = L"(A(B→C))";
    answer = L"2";
    wcout << L"Является ли строка формулой сокращенного языка логики высказываний?" << endl;
    wcout << formulaCheck << endl;
    wcout << L"\t1. Да\n\t2. Нет" << endl;
    getline(wcin, choice);
    if (answer == choice)
        wcout << L"Верно." << endl;
    else
        wcout << L"Неверно." << endl;
    printResult(checkStrIsFormula(formulaCheck));

    formulaCheck = L"(¬A)";
    answer = L"1";
    wcout << L"Является ли строка формулой сокращенного языка логики высказываний?" << endl;
    wcout << formulaCheck << endl;
    wcout << L"\t1. Да\n\t2. Нет" << endl;
    getline(wcin, choice);
    if (answer == choice)
        wcout << L"Верно." << endl;
    else
        wcout << L"Неверно." << endl;
    printResult(checkStrIsFormula(formulaCheck));

    formulaCheck = L"T2";
    answer = L"1";
    wcout << L"Является ли строка формулой сокращенного языка логики высказываний?" << endl;
    wcout << formulaCheck << endl;
    wcout << L"\t1. Да\n\t2. Нет" << endl;
    getline(wcin, choice);
    if (answer == choice)
        wcout << L"Верно." << endl;
    else
        wcout << L"Неверно." << endl;
    printResult(checkStrIsFormula(formulaCheck));
    ;

    formulaCheck = L"(A∨(B~C)";
    answer = L"2";
    wcout << L"Является ли строка формулой сокращенного языка логики высказываний?" << endl;
    wcout << formulaCheck << endl;
    wcout << L"\t1. Да\n\t2. Нет" << endl;
    getline(wcin, choice);
    if (answer == choice)
        wcout << L"Верно." << endl;
    else
        wcout << L"Неверно." << endl;
    printResult(checkStrIsFormula(formulaCheck));
}

int main()
{
    locale::global(locale(""));

    wstring str_formulaText;
    while (true)
    {
        wcout << L"\nСимвол логической лжи: 0" << endl;
        wcout << L"Символ логической правды: 1" << endl;
        wcout << L"Символ логического ИЛИ: \\/" << endl;
        wcout << L"Символ логического И: /\\" << endl;
        wcout << L"Символ логического отрицания: !" << endl;
        wcout << L"Символ логической импликации: ->" << endl;
        wcout << L"Символ логической эквиваленции:~" << endl;

        wcout << L"\nВведите строку для проверки: ";
        getline(wcin, str_formulaText);

        if (str_formulaText.empty())
            break;

        wcout << str_formulaText << endl;
        bool result = checkStrIsFormula(str_formulaText);
        printResult(result);
    }
    checkUser();
}
