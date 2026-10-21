# Индивидуальная лабораторная работа 1 по дисциплине МРЗвИС вариант 1
# Выполнена студентом группы 321701 БГУИР  Струнец Дмитрий Петрович
# Файл для получения входных аргументов программы
#
# Использованные источники:
# Формальные модели обработки информации и параллельные модели решения задач. Практикум: учебно-методическое пособие / В.П.Ивашенко. – Минск: БГУИР, 2020.

import argparse


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("input", help="Path to the input image")

    parser.add_argument(
        "--output", "-o", default="pictures/out.bmp", help="Output image path"
    )
    parser.add_argument(
        "--max-epoch", "-me", type=int, default=1000000, help="Number of max epochs"
    )
    parser.add_argument(
        "--max-error", "-merr", type=float, default=3000, help="The max error"
    )
    parser.add_argument("--lr", type=float, default=0.0002, help="Learning rate")
    parser.add_argument("-m", type=int, default=8, help="Width of blocks")
    parser.add_argument("-n", type=int, default=8, help="Height of blocks")
    parser.add_argument(
        "--secret-layer", "-sl", type=int, help="Amount of neurons on secret layer"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Seed for weight initialization"
    )

    return parser.parse_args()
