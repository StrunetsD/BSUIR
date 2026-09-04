#Лабораторная работа 2 по дисциплине 'Модели решения задач в интеллектуальных системах'
#Реализация модели решения задач в интеллектуальных системах
#Выполнил: студент гр.321701  Струнец Д.П.
# #Вариант 7: (~) = /2\\; /~\\ = /1\\; x~>y = max({1-x}\\/{y})
#Модели решения задач в интеллектуальных системах.
#В 2 ч. Ч.1: Формальные модели обработки информации и параллельные модели решения задач:
#учеб.-метод. пособие/ В. П. Ивашенко. – Минск : БГУИР, 2020. – 79 с.
#01.05.2026


import random
import math

ALFABET = [str(i) for i in range(10)]
A, B, E, G, C = [], [], [], [], []
Tn = 0
p, q, m = 0, 0, 0
sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
t_sum, t_mult, t_diff, t_comparison, n, r = 1, 1, 1, 1, 1, 1
Lavg, Tavg = 0, 0


# Сложение двух чисел; увеличивает счётчик сложений для расчёта последовательного времени T1.
def sum(a, b):
    global sum_call
    sum_call += 1
    return a + b


# Умножение двух чисел; увеличивает счётчик умножений для расчёта T1.
def mult(a, b):
    global mult_call
    mult_call += 1
    return a * b


# Вычитание (a − b); увеличивает счётчик вычитаний для расчёта T1.
def diff(a, b):
    global diff_call
    diff_call += 1
    return a - b


# Сравнение: возвращает max или min в зависимости от флага; учитывается в счётчике сравнений для T1.
def compare(a, b, max_or_min):
    global compare_call
    compare_call += 1
    if (max_or_min):
        return max(a, b)
    else:
        return min(a, b)


# Проверка строки ввода: 0 — только цифры; 1 — есть недопустимые символы.
def check_input(str):
    for i in str:
        if i not in ALFABET:
            return 1
    return 0


# Вывод матрицы в консоль с необязательным заголовком name.
def print_matrix(matr, name=''):
    print(name)
    for row in matr:
        string = "   "
        for col in row:
            string += str(col) + "  "
        print(string)


# Заполнение глобальных матриц A, B, E, G случайными числами из [-1; 1] с округлением до 3 знаков.
def fill_matrix(m, p, q):
    global A, B, E, G
    A = [[round(random.uniform(-1, 1.001), 3) for _ in range(m)] for i in range(p)]
    B = [[round(random.uniform(-1, 1.001), 3) for _ in range(q)] for i in range(m)]
    E = [[round(random.uniform(-1, 1.001), 3) for _ in range(m)] for i in range(1)]
    G = [[round(random.uniform(-1, 1.001), 3) for _ in range(q)] for i in range(p)]


# Аналитическая суммарная «длина» решения Tavg по формулам из методички (блоки f, d, агрегации по k, c).
def find_Tavg():
    Tavg = 0
    Tavg += p * q * m * (3 * (t_diff + t_comparison) + 7 * t_mult + 3 * t_diff + 2 * t_sum)  # f[i][j][k]
    Tavg += p * q * m * t_comparison  # d[i][j][k]
    Tavg += p * q * (m - 1) * t_mult  # /~\k
    Tavg += p * q * ((m + 1) * t_diff + (m - 1) * t_mult)  # \~/k
    Tavg += p * q * (7 * t_mult + 2 * t_sum + 3 * t_diff + t_mult)  # c[i][j]
    return Tavg


# Вычисляет матрицу C размером x×y по варианту 7; внутри — вложенные функции f, d и элемент C[i][j], учёт Tn.
def find_C(x, y, m):
    global C

    # Конъюнкция (произведение двух значений) для промежуточных формул.
    def find_compose(a, b):  # a * b
        return mult(a, b)

    # t-норма Лукасевича как min(a, b).
    def find_tnorm(a, b):  # min(a,b)
        return compare(a, b, 0)

    # Импликация варианта 7: max(1 − a, b).
    def find_impl(a, b):  # max(1 - a,b)
        return compare(diff(1, a), b, 1)

    # Агрегация /~\ по k для f(i,j): произведение по k выражений из A, B, E; корректировка Tn под параллелизм по k.
    def find_kf(i, j):
        # f = a_to_b*(2*E[0][k]-1)*E[0][k] + b_to_a*(1+(4*a_to_b-2)*E[0][k])*(1-E[0][k])
        global A, B, E, G, mult_call, diff_call, sum_call, compare_call, n, Tn, p, q, m, Tavg
        multipl_arr = []
        old_Tn = Tn

        for k in range(m):
            a_to_b = find_impl(A[i][k], B[k][j])
            b_to_a = find_impl(B[k][j], A[i][k])
            temp1 = mult(mult(a_to_b, diff(mult(2, E[0][k]), 1)), E[0][k])
            temp2 = mult(mult(b_to_a, sum(1, (mult(diff(mult(4, a_to_b), 2), E[0][k])))), diff(1, E[0][k]))
            # print(f"f00{k}: " + str(temp1 + temp2))
            multipl_arr.append(sum(temp1, temp2))

            Tn += math.ceil(3 / n) * t_diff
            Tn += 1 * t_mult
            Tn += math.ceil(2 / n) * t_comparison
            Tn += 1 * t_mult
            Tn += math.ceil(2 / n) * t_diff
            Tn += math.ceil(2 / n) * t_mult
            Tn += 1 * t_mult
            Tn += 1 * t_sum
            Tn += 1 * t_mult
            Tn += 1 * t_mult
            Tn += 1 * t_sum

        if 6 <= n <= m * 3:
            new_n = n - n % 3  # будет задействоваться максимальное n кратное 3
            count = math.ceil((m * 3) / new_n)  # сколько должно выполниться последовательных операций
            temp = (Tn - old_Tn) / m  # сколько по времени одна итерация
            Tn = Tn - (m - count) * temp  # отнимаем операции, которые можно распараллелить
        elif n >= m * 3:
            temp = (Tn - old_Tn) / m
            Tn = old_Tn + temp

        kf = multipl_arr[0]
        for i_mult in range(1, len(multipl_arr)):
            kf = mult(kf, multipl_arr[i_mult])

        Tn += math.ceil(m - 1) * t_mult

        # print("kf: " + str(kf))
        return kf

    # Агрегация ~\ по k для d(i,j): вероятностная сумма через произведение (1 − min(A,B)), затем 1 − результат.
    def find_kd(i, j):
        nonlocal m
        global A, B, mult_call, diff_call, sum_call, compare_call, n, Tn, Tavg, q, p
        multipl_arr = []
        old_Tn = Tn

        for k in range(m):
            temp1 = find_tnorm(A[i][k], B[k][j])
            # print(f"d00{k}:" + str(temp1))
            temp2 = diff(1, temp1)
            multipl_arr.append(temp2)
            Tn += 1 * t_comparison
            Tn += 1 * t_diff


        if 2 <= n <= m * 1:
            new_n = n - n % 1  # будет задействоваться максимальное n кратное 1
            count = math.ceil((m * 1) / new_n)  # сколько должно выполниться последоватеьных операций
            temp = (Tn - old_Tn) / m  # сколько по времени одна итерация
            Tn = Tn - (m - count) * temp  # отнимаем операции, которые можно распараллелить
        elif n >= m * 1:
            temp = (Tn - old_Tn) / m
            Tn = old_Tn + temp


        dd_res = multipl_arr[0]
        for i_mult in range(1, len(multipl_arr)):
            dd_res = mult(dd_res, multipl_arr[i_mult])
        dd = diff(1, dd_res)
        # print("kd: " + str(dd))

        Tn += math.ceil(m - 1) * t_mult
        Tn += 1 * t_diff

        return dd

    # Одно значение C[i][j] из f, d, G по формуле задания; добавляет вклад в параллельное время Tn.
    def find_cij(i, j):
        # cij = f*(3*G[i][j] - 2)*G[i][j] + (d+(4*f_and_d-3*d)*G[i][j])*(1-G[i][j])
        global A, B, E, G, sum_call, diff_call, mult_call, compare_call, n, Tn
        d = find_kd(i, j)  # with \~/k
        f = find_kf(i, j)  # with /~\k


        f_and_d = find_compose(f, d)
        # print("f_d: ", f_and_d)
        cij = sum(mult(mult(f, diff(mult(3, G[i][j]), 2)), G[i][j]),
                  mult(sum(d, mult(diff(mult(4, f_and_d), mult(3, d)), G[i][j])), diff(1, G[i][j])))
        Tn += 1 * t_mult
        Tn += math.ceil(3 / n) * t_mult
        Tn += math.ceil(3 / n) * t_diff
        Tn += math.ceil(2 / n) * t_mult
        Tn += 1 * t_mult
        Tn += math.ceil(2 / n) * t_mult
        Tn += 1 * t_sum

        # print(f"C[{i}][{j}] = {cij}\n")
        return cij

    C = [[find_cij(i, j) for j in range(y)] for i in range(x)]


# Интерактивный ввод m, p, q, n; генерация данных, расчёт C и метрик T1, Tn, Ky, e, r, Lavg, D; печать матриц.
def main():
    global p, q, m, Tn, n
    #n - кол-во процессорных элементов
    #m p q - размеры матриц
    while (1):
        m = input("m = ")
        p = input("p = ")
        q = input("q = ")
        n = input("n = ")
        # t_sum = int(input("Время операции суммирования: "))
        # t_mult = int(input("Время операции умножения: "))
        # t_diff = int(input("Время операции вычитания: "))
        # t_comparison = int(input("Время операции сравнения: "))
        print("\n")
        if (check_input(m + p + q + n)):
            print("Некорректный ввод")
            continue
        elif int(n) == 0 or int(p) == 0 or int(m) == 0 or int(q) == 0:
            print("Введите значения больше 0")
            continue
        else:
            p = int(p)
            q = int(q)
            m = int(m)
            fill_matrix(m, p, q)
            n = int(n)
            find_C(int(p), int(q), int(m))
            break

    T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
    Ky = T1 / Tn
    e = Ky / n
    r = p * q + p * m + q * m + 1 * m + p * q
    Tavg = find_Tavg()
    Lavg = Tavg/r
    D = Tn / Lavg

    print_matrix(A, "\nA:")
    print_matrix(B, "\nB:"),
    print_matrix(E, "\nE:")
    print_matrix(G, "\nG:")
    print_matrix(C, "\nC:")

    print("\nParametrs:")
    print("T1 = " + str(T1)) # последовательное ( архитек.) выполнение кода
    print("Tn = " + str(Tn)) #  параллельное ( архитек.) выполнение кода
    print("r = " + str(r))
    print("Ky = " + str(Ky)) # коэфф. ускорения T1/Tn
    print("e = " + str(e)) # эффективность Ky/n
    print("Lsum = " + str(Tn)) #  суммарная длина программы на праллельной архит.
    print("Lavg = " + str(Lavg)) # среднее решение задач праллельной архит.
    print("D = " + str(D))# коэфф. расхождения Lsum/Lavg


# График коэффициента ускорения Ky от ранга r при фиксированных n = 10 и n = 7 (m = p = q растут от 1 до 20).
def main_graphicsKr():
    import matplotlib.pyplot as plt

    global p, q, m, Tn, sum_call, mult_call, diff_call, compare_call, n, Tavg
    t_mult, t_diff, t_sum, t_comparison = 1, 1, 1, 1  # задаём времена операций
    ky_n10 = []
    ky_n7 = []
    r_vals = []

    for i in range(20):
        # --- n = 10 ---
        Tn, Tavg = 0, 0
        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
        m = p = q = i + 1
        n = 10
        fill_matrix(m, p, q)
        find_C(p, q, m)
        r = p * q + q * m + p * m + m + p * q
        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
        Ky = T1 / Tn
        ky_n10.append(Ky)
        print(f"n = {n}, m = {m}, r = {r}, T1 = {T1}, Tn = {Tn}, Ky = {Ky}")
        r_vals.append(r)

    for i in range(20):
        # --- n = 7 ---
        Tn, Tavg = 0, 0
        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
        m = p = q = i + 1
        n = 7
        fill_matrix(m, p, q)
        find_C(p, q, m)
        # r = p * q + q * m + p * m + m + p * q
        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
        Ky = T1 / Tn
        print(f"n = {n}, m = {m}, r = {r}, T1 = {T1}, Tn = {Tn}, Ky = {Ky}")
        ky_n7.append(Ky)

    plt.figure(figsize=(10, 5))
    plt.plot(r_vals, ky_n10, 'k', label='n = 10', linewidth=2)
    plt.plot(r_vals, ky_n7, label='n = 7', linewidth=3)
    plt.xlabel('r', fontsize=14)
    plt.ylabel('Ky(r)', fontsize=14)
    plt.grid(True)
    plt.legend(loc='best', fontsize=12)
    plt.show()


# График Ky(n) при фиксированном ранге задачи r = 40 и r = 33 (подбор p, q, m в диапазоне 1..10).
def main_graphicsKyn():
    import matplotlib.pyplot as plt

    global p, q, m, Tn, sum_call, mult_call, diff_call, compare_call, n, Tavg
    t_mult, t_diff, t_sum, t_comparison = 1, 1, 1, 1
    x = []
    ky_40 = []

    for n in range(1, 51):
        found = False
        for p in range(1, 11):
            for q in range(1, 11):
                for m in range(1, 11):
                    r = p * q + q * m + p * m + m + p * q
                    if r == 40:
                        Tn, Tavg = 0, 0
                        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
                        fill_matrix(m, p, q)
                        find_C(p, q, m)
                        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
                        Ky = T1 / Tn
                        # print(f"n = {n}, m = {m}, r = {r}, T1 = {T1}, Tn = {Tn}, Ky = {Ky}")
                        ky_40.append(Ky)
                        x.append(n)
                        found = True
                        break
                if found:
                    break
            if found:
                break

    x2 = []  # значения n для r = 33
    ky_33 = []

    for n in range(1, 51):
        found = False
        for p in range(1, 11):
            for q in range(1, 11):
                for m in range(1, 11):
                    r = p * q + q * m + p * m + m + p * q
                    if r == 33:
                        Tn, Tavg = 0, 0
                        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
                        fill_matrix(m, p, q)
                        find_C(p, q, m)
                        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
                        Ky = T1 / Tn
                        # print(f"n = {n}, m = {m}, r = {r}, T1 = {T1}, Tn = {Tn}, Ky = {Ky}")
                        ky_33.append(Ky)
                        x2.append(n)
                        found = True
                        break
                if found:
                    break
            if found:
                break

    # Построение графика
    plt.figure(figsize=(10, 5))
    # print(ky_40)
    # print(ky_33)
    plt.plot(x, ky_40, 'k', label='r = 40', linewidth=2)
    plt.plot(x2, ky_33, label='r = 33', linewidth=3)
    plt.xlabel('n', fontsize=14)
    plt.ylabel('Ky(n)', fontsize=14)
    plt.grid(True)
    plt.legend(loc='best', fontsize=12)
    plt.show()


# График эффективности e(r) = Ky/n при n = 10 и n = 7 при росте m = p = q.
def main_graphicsEr():
    import matplotlib.pyplot as plt

    global p, q, m, Tn, sum_call, mult_call, diff_call, compare_call, n, Tavg
    t_mult, t_diff, t_sum, t_comparison = 1, 1, 1, 1  # задаём времена операций
    e_n7 = []
    e_n10 = []
    r_vals = []

    for i in range(20):
        # --- n = 10 ---
        Tn, Tavg = 0, 0
        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
        m = p = q = i + 1
        n = 10
        fill_matrix(m, p, q)
        find_C(p, q, m)
        r = p * q + q * m + p * m + m + p * q
        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
        Ky = T1 / Tn
        e = Ky / n
        # print(f"n = {n}, m = {m}, r = {r}, T1 = {T1}, Tn = {Tn}, Ky = {Ky}, e = {e}")
        e_n10.append(e)
        r_vals.append(r)

    for i in range(20):
        # --- n = 7 ---
        Tn, Tavg = 0, 0
        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
        m = p = q = i + 1
        n = 7
        fill_matrix(m, p, q)
        find_C(p, q, m)
        r = p * q + q * m + p * m + m + p * q
        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
        Ky = T1 / Tn
        e = Ky / n
        # print(f"n = {n}, m = {m}, r = {r}, T1 = {T1}, Tn = {Tn}, Ky = {Ky}, e = {e}")
        e_n7.append(e)

    plt.figure(figsize=(10, 5))
    plt.plot(r_vals, e_n10, 'k', label='n = 10', linewidth=2)
    plt.plot(r_vals, e_n7, label='n = 7', linewidth=3)
    plt.xlabel('r', fontsize=14)
    plt.ylabel('e(r)', fontsize=14)
    plt.grid(True)
    plt.legend(loc='best', fontsize=12)
    plt.show()


# График e(n) при фиксированных r = 40 и r = 33.
def main_graphicsEn():
    import matplotlib.pyplot as plt

    global p, q, m, Tn, sum_call, mult_call, diff_call, compare_call, n, Tavg
    t_mult, t_diff, t_sum, t_comparison = 1, 1, 1, 1
    x = []   # значения n для r = 40
    e_40 = []

    for n in range(1, 51):
        found = False
        for p in range(1, 11):
            for q in range(1, 11):
                for m in range(1, 11):
                    r = p * q + q * m + p * m + m + p * q
                    if r == 40:
                        Tn, Tavg = 0, 0
                        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
                        fill_matrix(m, p, q)
                        find_C(p, q, m)
                        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
                        Ky = T1 / Tn if Tn != 0 else 0
                        e = Ky / n
                        e_40.append(e)
                        x.append(n)
                        found = True
                        break
                if found:
                    break
            if found:
                break

    x2 = []  # значения n для r = 33
    e_33 = []

    for n in range(1, 51):
        found = False
        for p in range(1, 11):
            for q in range(1, 11):
                for m in range(1, 11):
                    r = p * q + q * m + p * m + m + p * q
                    if r == 33:
                        Tn, Tavg = 0, 0
                        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
                        fill_matrix(m, p, q)
                        find_C(p, q, m)
                        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
                        Ky = T1 / Tn if Tn != 0 else 0
                        e = Ky / n
                        e_33.append(e)
                        x2.append(n)
                        found = True
                        break
                if found:
                    break
            if found:
                break


    plt.figure(figsize=(10, 5))
    plt.plot(x, e_40, 'k', label='r = 40', linewidth=2)
    plt.plot(x2, e_33, label='r = 33', linewidth=3)
    plt.xlabel('n', fontsize=14)
    plt.ylabel('e(n)', fontsize=14)
    plt.grid(True)
    plt.legend(loc='best', fontsize=12)
    plt.show()


# График коэффициента расхождения D(r) = Tn/Lavg для двух значений n (10 и 7), m = p = q от 1 до 10.
def main_graphicsDr():
    global p, q, m, Tn, sum_call, mult_call, diff_call, compare_call, n, Tavg
    x = []
    d_ = []
    ky_ = []

    for i in range(10):
        Tn, Tavg = 0, 0
        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
        m = i + 1
        p = i + 1
        q = i + 1
        n = 10
        fill_matrix(int(m), int(p), int(q))
        find_C(int(p), int(q), int(m))
        r = p * q + q * m + p * m + 1 * m + p * q
        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
        Ky = T1 / Tn
        e = Ky / n
        Tavg = find_Tavg()
        Lavg = Tavg / r
        D = Tn / Lavg
        ky_.append(Ky)
        d_.append(D)
        x.append(r)
    y2 = []
    for i in range(10):
        Tn, Tavg = 0, 0
        sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
        m = i + 1
        p = i + 1
        q = i + 1
        n = 7
        fill_matrix(int(m), int(p), int(q))
        find_C(int(p), int(q), int(m))
        r = p * q + q * m + p * m + 1 * m + p * q
        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
        Ky = T1 / Tn
        e = Ky / n
        Tavg = find_Tavg()
        Lavg = Tavg / r
        D = Tn / Lavg
        ky_.append(Ky)
        y2.append(D)

    import matplotlib.pyplot as plt
    y = d_
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, 'k', label='n = 10', linewidth=2)
    plt.plot(x, y2, label="n = 7", linewidth=3)
    plt.xlabel('r', fontsize=14)
    plt.ylabel('D(r)', fontsize=14)
    plt.grid(True)
    plt.legend(loc='best', fontsize=12)
    plt.show()





# График D(n) при фиксированных r = 33 и r = 40 (перебор p, q, m и n от 1 до 50).
def main_graphicsDn():
    global p, q, m, Tn, sum_call, mult_call, diff_call, compare_call, n, Tavg
    x = []
    d_ = []
    ky_ = []

    for n in range(1, 51):
        for p in range(1, 11):
            for q in range(1, 11):
                for m in range(1, 11):
                    Tn, Tavg = 0, 0
                    sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
                    r = p * q + q * m + p * m + 1 * m + p * q
                    if r == 33:
                        fill_matrix(int(m), int(p), int(q))
                        find_C(int(p), int(q), int(m))
                        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
                        Ky = T1 / Tn
                        e = Ky / n
                        Tavg = find_Tavg()
                        Lavg = Tavg / r
                        D = Tn / Lavg
                        # print(f"n = {n}, r = {r}, m = {m}, Tn = {Tn}, Lavg = {Lavg}, D = {D}")
                        ky_.append(Ky)
                        d_.append(D)
                        x.append(n)
                        break  # Нашли подходящие p, q, m, выходим из цикла
                else:
                    continue
                break
            else:
                continue
            break

    y2 = []
    x2 = []
    for n in range(1, 51):
        for p in range(1, 11):
            for q in range(1, 11):
                for m in range(1, 11):
                    Tn, Tavg = 0, 0
                    sum_call, mult_call, diff_call, compare_call = 0, 0, 0, 0
                    r = p * q + q * m + p * m + 1 * m + p * q
                    if r == 40:
                        fill_matrix(int(m), int(p), int(q))
                        find_C(int(p), int(q), int(m))
                        T1 = mult_call * t_mult + diff_call * t_diff + sum_call * t_sum + compare_call * t_comparison
                        Ky = T1 / Tn
                        e = Ky / n
                        Tavg = find_Tavg()
                        Lavg = Tavg / r
                        D = Tn / Lavg
                        # print(f"n = {n}, r = {r}, m = {m}, Tn = {Tn}, Lavg = {Lavg}, D = {D}")
                        ky_.append(Ky)
                        y2.append(D)
                        x2.append(n)
                        break
                else:
                    continue
                break
            else:
                continue
            break

    import matplotlib.pyplot as plt
    y = d_
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, 'k', label='r = 33', linewidth=2)
    plt.plot(x2, y2, label="r = 40", linewidth=3)
    plt.xlabel('n', fontsize=14)
    plt.ylabel('D(n)', fontsize=14)
    plt.grid(True)
    plt.legend(loc='best', fontsize=12)
    plt.show()

main()


#main_graphicsKr()
# main_graphicsKyn()
# main_graphicsEr()
# main_graphicsEn()
# main_graphicsDr()
# main_graphicsDn()