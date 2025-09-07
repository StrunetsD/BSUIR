import random


def factorization(num):
    prime_factors = []
    for i in range(2, num):
        if num % i == 0:
            prime_factors.append(i)
            while num % i == 0:
                num //= i
    if num > 1:
        prime_factors.append(num)
    return prime_factors


def find_g(p):
    fact_res = factorization(p - 1)
    degrees = []
    for denominator in fact_res:
        degrees.append(int((p - 1) / denominator))
    for i in range(2, p-1):
        b = True
        for j in degrees:
            if exponentiation(i, j, p) == 1: 
                b = False
                break
        if b == 1 and (i ** (p - 1)) % p == 1:
            return i
    return 0


def exponentiation(x, degree, p):
    result = x
    bit_degree = bin(degree)[3:]
    for i in bit_degree:
        result = ((result**2) * x) % p\
            if i == '1'\
            else (result ** 2) % p
    return result 


p = 9679
g = find_g(p)
print(f'Простое число Р: {p}, первообразный корень g: {g}')

a = random.choice(range(1, p))
A = exponentiation(g, a, p)
print(f'Алиса генерирует а: {a}, вычисляет А и отправляет Бобу: {A}')

b = random.choice(range(1, p))
B = exponentiation(g, b, p)
print(f'Боб генерирует b: {b}, вычисляет В и отправляет Алисе: {B}')

key_a = exponentiation(B, a, p)
key_b = exponentiation(A, b, p)
print(f"Алиса и Боб вычисляют ключ: {key_a} = {key_b}")