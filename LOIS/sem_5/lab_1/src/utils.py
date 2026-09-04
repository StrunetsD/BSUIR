'''
Лабораторная работа №1
по дисциплине ЛОИС
Выполнена студентами группы 321701
Cтрунец Дмитрий Петрович, Леоненко Максим Николаевич, Старовойтов Артем Игорьевич 
Вариант 1:
Реализовать прямой нечеткий логический вывод используя импликацию Геделя
'''
from prettytable import PrettyTable


def print_table(name, table):
    pretty_table = PrettyTable()
    rows_names = list(table.keys())
    cols_names = [name, *list(table[rows_names[0]].keys())]
    pretty_table.field_names = cols_names
    precision = 5
    for row_name in rows_names:
        rounded_values = [
            round(value, precision) if isinstance(value, float) else value 
            for value in table[row_name].values()
        ]
        pretty_table.add_row([row_name, *rounded_values])
    
    print(pretty_table)