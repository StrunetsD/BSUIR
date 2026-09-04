'''
Лабораторная работа №1
по дисциплине ЛОИС
Выполнена студентами группы 321701
Cтрунец Дмитрий Петрович, Леоненко Максим Николаевич, Старовойтов Артем Игорьевич 
Вариант 1:
Реализовать прямой нечеткий логический вывод используя импликацию Геделя
'''
def gedel_impl(v1, v2):
    return 1 if v1 <= v2 else v2


def matrix_impl(set1, set2):
    return {i: {j: gedel_impl(set1[i], set2[j]) for j in set2} for i in set1}


def t_norm(v1, v2):
    return min(v1, v2)


def built_impl_table(set1, relation):
    if set(set1.keys()) != set(relation.keys()):
        raise ValueError(f"{set(set1.keys())} != {set(relation.keys())}")
    return {i: {j: t_norm(set1[i], relation[i][j]) for j in relation[i]} for i in relation}


def compress(impl_table):
    row_keys = list(impl_table.keys())
    col_keys = list(impl_table[row_keys[0]].keys())
    return {col_key: max([impl_table[row_key][col_key] for row_key in row_keys]) for col_key in col_keys}