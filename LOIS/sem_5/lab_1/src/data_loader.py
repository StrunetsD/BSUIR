'''
Лабораторная работа №1
по дисциплине ЛОИС
Выполнена студентами группы 321701
Cтрунец Дмитрий Петрович, Леоненко Максим Николаевич, Старовойтов Артем Игорьевич 
Вариант 1:
Реализовать прямой нечеткий логический вывод используя импликацию Геделя
'''
from typing import List

from .data_validators import *


def load_from_file(path):
    facts, functions = None, None
    with open(path, "r") as file:
        facts, functions = (tuple("".join(x.split()) for x in line.split("\n")) for line in file.read().split("\n\n"))
    facts = [Fact(fact) for fact in facts]
    functions = [Function(function) for function in functions]
    return get_facts_dict(facts), get_functions_dict(functions)


def get_facts_dict(facts: List[Fact]):
    return {fact.head_without_variables: fact for fact in facts}

def get_functions_dict(functions: List[Function]):
    return {func.head_without_variables: func for func in functions}


    