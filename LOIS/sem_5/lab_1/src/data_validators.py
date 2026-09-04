'''
Лабораторная работа №1
по дисциплине ЛОИС
Выполнена студентами группы 321701
Cтрунец Дмитрий Петрович, Леоненко Максим Николаевич, Старовойтов Артем Игорьевич 
Вариант 1:
Реализовать прямой нечеткий логический вывод используя импликацию Геделя
'''
import re


def remove_variables(head: str):
    name = head.split("(")[0]
    num_of_comma = head.count(",")
    return f"{name}({',' * num_of_comma})"

class Fact:
    class InvalidFactExeption(Exception):
        def __init__(self, fact: str) -> None:
            super().__init__(f"Invalid format of fact: {fact}")

    def __init__(self, fact: str, valid_check=True) -> None:
        self.fact = fact
        if valid_check and not self.__is_valid():
            raise Fact.InvalidFactExeption(fact)
        self.head = self.__get_head()
        self.head_without_variables = remove_variables(self.head)
        self.tail = self.__get_tail()
        if not self.__tail_is_valid():
            raise Fact.InvalidFactExeption(fact)
        self.tail = {pair[0]: pair[1] for pair in self.tail}

    def __is_valid(self):
        # Регулярное выражение можно адаптировать, если потребуется
        pattern = re.compile(r"^[a-z]\([a-z]\)={(\([a-z],\d+(\.\d+)?\),)*(\([a-z],\d+(\.\d+)?\))?}$")
        return bool(pattern.match(self.fact))

    def __get_head(self):
        head_tail_pattern = r"^(.+)={(.*)}$"
        return re.match(head_tail_pattern, self.fact).group(1)

    def __get_tail(self):
        head_tail_pattern = r"^(.+)={(.*)}$"
        pairs_str = re.match(head_tail_pattern, self.fact).group(2)
        pairs = [tuple(pair.split(",")) for pair in pairs_str[1:-1].split("),(")]

        def validate_value(x):
            val = float(x)
            if val > 1 or val < 0:
                raise Fact.InvalidFactExeption(f"Value {val} must be between 0 and 1 (inclusive)")
            return val

        return tuple() if len(pairs[0]) == 1 else tuple((x[0], validate_value(x[1])) for x in pairs)

    def __tail_is_valid(self):
        return len(set(map(lambda x: x[0], self.tail))) == len(list(map(lambda x: x[0], self.tail)))



class Function:

    class InvalidFunctionExeption(Exception):
        def __init__(self, func: str) -> None:
            super().__init__(f"Invalid format of function: {func}")

    def __init__(self, func: str) -> None:
        self.func = func
        if not self.__is_valid():
            raise Function.InvalidFunctionExeption(func)
        self.head = self.__get_head()
        self.head_without_variables = remove_variables(self.head)
        self.tail = self.__get_tail()
        self.tail_without_variables = tuple(remove_variables(x) for x in self.tail)

    def __is_valid(self):
        pattern = re.compile(r"^[a-z]\(([a-z],)*[a-z]\)=\([a-z]\([a-z]\)~>[a-z]\([a-z]\)\)$")
        return bool(pattern.match(self.func))
    
    def __get_head(self):
        head_tail_pattern = r"^(.+)=(.*)$"
        return re.match(head_tail_pattern, self.func).group(1)

    def __get_tail(self):
        head_tail_pattern = r"^(.+)=(.*)$"
        pairs_str = re.match(head_tail_pattern, self.func).group(2)
        return tuple(pairs_str[1:-1].split("~>"))