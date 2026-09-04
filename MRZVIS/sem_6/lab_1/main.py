# Лабораторная работа №1 по дисциплине Модели решения задач в интеллектуальных системах.
# Вариант 10. Реализовать алгоритм вычисления произведения пары 6-разрядных чисел умножением со старших разрядов со сдвигом частичной суммы влево.
# Выполнена студентом группы 321701 БГУИР Струнец Дмитрий Петрович
# Программа выполняет умножение пары чисел.

import sys
import os

def check_values(a, b):
    if a > 63 or b > 63:
        return False
    return True

def sum(p: str, s: str) -> str:
    result = ''
    carry = 0

    max_len = max(len(p), len(s))
    p = p.zfill(max_len)
    s = s.zfill(max_len)

    for i in range(max_len - 1, -1, -1):
        bit1 = int(p[i])
        bit2 = int(s[i])
        total = bit1 + bit2 + carry
        result = str(total % 2) + result
        carry = total // 2

    # Добавляем оставшийся перенос, если есть
    if carry:
        result = '1' + result

    # Обрезаем или дополняем до 12 бит
    if len(result) > 12:
        result = result[-12:]  # оставляем младшие 12 бит
    else:
        result = result.zfill(12)

    return result


def algorithm(list):
    a = list[0]
    b = list[1]
    pp = list[2]
    ps = list[3]
    if b[0] == '1':
        pp = '0'*6 + a
        ps = sum(ps, pp)
    return [a, b, pp, ps]

def print_tact(queue, steps, res, tact):
    print("такт", tact+1)
    print("Входная очередь:")
    for i in range(len(queue)):
        print(queue[i][0], "и", queue[i][1])
    if len(queue) == 0:
        print("-")
    for i in range(6):
        print("этап", i+1)
        if len(steps[i]) != 0:
            print("множимое: ", steps[i][0])
            print("множитель: ", steps[i][1])
            print("частичное произведение: ", steps[i][2])
            print("частичная сумма: ", steps[i][3])
        else: 
            print("-")

    if len(res) != 0 :
        print("Результат: " )
        for i in res:
            print(i, "("+str(int(i, 2))+")")
    print("1. Дальше")
    print("2. Выход")
    i = input()
    if i == '1':
        os.system('cls' if os.name == 'nt' else 'clear')
        return 
    else:
        sys.exit()

def main():
    while True:
        print("введите вектор А: ")
        first = input()
        print("введите вектор В: ")
        second = input()

        A = [int(num.strip()) for num in first.split(',') if num.strip().isdigit()]
        B = [int(num.strip()) for num in second.split(',') if num.strip().isdigit()]

        if len(A) != len(B):
            print("не совпадают размеры векторов")
            return
        
        check = True
        for i in range(len(A)):
            is_check = check_values(A[i], B[i])
            if not is_check:
                check = False

        if not check:
            print("разряд числа превышает 6")
            return
        
        takt_size = 6 + len(A) - 1
        
        queue = [[A[i], B[i]] for i in range(len(A))]
        queue_for_result = queue
        steps = [[], [], [], [], [], []]
        res = []

        data = []

        for i in queue:
            a = bin(i[0])[2:]
            b = bin(i[1])[2:]
            a = '0'*(6-len(a)) + a
            b = '0'*(6-len(b)) + b
            pp = '0'*12
            ps = pp
            data.append([a, b, pp, ps])

        print_tact(queue, steps, res, -1)
        queue = queue[1:]
        for i in range(takt_size):
            j = i
            
            if j-len(A) < 0 :
                end = -1
            else: end = j-len(A)

            if j > 5:
                j = 5
            
            while j != end:
                if j == 0:
                    step = algorithm(data[0])
                    data = data[1:]
                    steps[0] = step
                else:
                    data_from_step = steps[j-1]
                    data_from_step[1] = data_from_step[1][1:] + '0'
                    data_from_step[3] = data_from_step[3][1:] + '0'
                    step = algorithm(data_from_step)
                    steps[j] = step
                    steps[j-1] = []
                    if j == 5:
                        res.append(step[3])
                        
                j = j-1
            print_tact(queue, steps, res, i)
            if len(queue) != 0:
                queue = queue[1:]
        steps = [[],[],[],[],[],[]]
        print_tact(queue_for_result, steps, res, -1)



if __name__ == "__main__":
    main()
    
