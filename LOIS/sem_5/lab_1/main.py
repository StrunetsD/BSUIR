'''
Лабораторная работа №1
по дисциплине ЛОИС
Выполнена студентами группы 321701
Cтрунец Дмитрий Петрович, Леоненко Максим Николаевич, Старовойтов Артем Игорьевич 
Вариант 1:
Реализовать прямой нечеткий логический вывод используя импликацию Геделя
'''


from src import operations
from src.data_loader import load_from_file, get_facts_dict
from src.data_validators import Fact
from src.utils import print_table

import os


def main(dir: str):


    for i, filename in enumerate(sorted(os.listdir(dir))):

        print(f"{'-' * 10}{i + 1}{'-' * 10}")
        
        file = os.path.join(dir, filename)
        if not os.path.isfile(file):
            print(f"Skip {file} (isn't a file)")
            continue
        
        print("Input:")
        with open(file, "r") as f:
            print(f.read())
        print()

        print("Solution:")
        facts, functions = load_from_file(file)

        function_tables, function_tables_titles = {}, []
        for function_head, function_obj in functions.items():
            function_tables_titles.append(function_obj.head)
            first_set_name, second_set_name = function_obj.tail_without_variables
            first_set, second_set = facts[first_set_name], facts[second_set_name]
            function_tables[function_head] = operations.matrix_impl(first_set.tail, second_set.tail)

        for table_title, table_tail in zip(function_tables_titles, function_tables.values()):
            print_table(table_title, table_tail)

            result_sets = []

            for table_title, function_table in zip(function_tables_titles, function_tables.values()):
                for fact in facts.values():
                    try:
                        
                        result_impl_table = operations.built_impl_table(fact.tail, function_table)

                        result_set_head = f"{table_title}/~/{fact.head}"
                        result_set_tail = operations.compress(result_impl_table)

                        print_table(result_set_head, result_impl_table)

                        result_sets.append("{" + ", ".join(f"({pair[0]}, {pair[1]})" for pair in result_set_tail.items()) + "}")
                        
                        
                    except ValueError:
                        ...
            print("Answer: ")
            facts = []
            for i, tail in enumerate(result_sets):
                name = f"{chr(97 + i)}(x)"
                print(f"{name} = {tail}")
                facts.append(f"{name}={tail.replace(' ', '')}")

            
            print()
            input()
            facts = get_facts_dict([Fact(fact) for fact in facts])


if __name__ == "__main__":
    main("data")

