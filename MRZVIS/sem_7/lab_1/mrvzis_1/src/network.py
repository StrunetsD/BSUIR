# Индивидуальная лабораторная работа 1 по дисциплине МРЗвИС вариант 1
# Выполнена студентом группы 321701 БГУИР  Струнец Дмитрий Петрович
# Файл реализации линейной рециркуляционной сети
#
# Использованные источники:
# Формальные модели обработки информации и параллельные модели решения задач. Практикум: учебно-методическое пособие / В.П.Ивашенко. – Минск: БГУИР, 2020.

import numpy as np


class Network:
    def __init__(
        self,
        input_size: int,
        output_size: int,
        learning_rate: float,
        max_error: float,
        max_epoch: int,
    ):
        self.input_size = input_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        self.max_error = max_error
        self.max_epoch = max_epoch
        self.init_weights((input_size, output_size))

    def init_weights(self, size: tuple[int, int]) -> None:
        self.W1 = np.random.uniform(-1, 1, size=size)
        self.W2 = np.random.uniform(-1, 1, size=size[::-1])

    def forward(self, input: np.ndarray) -> np.ndarray:
        self.encoded = input @ self.W1
        return self.encoded @ self.W2

    def backward(self, input: np.ndarray, output: np.ndarray) -> None:
        err = output - input

        W2_grad = self.encoded.T @ err

        W1_grad = input.T @ (err @ self.W2.T)

        self.W2 -= W2_grad * self.learning_rate
        self.W1 -= W1_grad * self.learning_rate

    def train_network(self, inputs: np.ndarray) -> int:
        """Обучает сеть по эпохам; возвращает число выполненных эпох."""
        cur_epoch = 0
        cur_error = float("inf")

        while cur_error >= self.max_error and cur_epoch < self.max_epoch:
            cur_epoch += 1

            for i in range(inputs.shape[0]):
                cur_input = inputs[i : i + 1, :]
                output = self.forward(cur_input)
                self.backward(cur_input, output)

            full_output = (inputs @ self.W1) @ self.W2
            cur_error = 0.5 * np.sum((full_output - inputs) ** 2)

            if not np.isfinite(cur_error):
                raise RuntimeError(
                    f"Обучение расходится на эпохе {cur_epoch}: "
                    "уменьшите коэффициент обучения (--lr)."
                )

            print(f"Epoch {cur_epoch}, error = {cur_error:.6f}")

        return cur_epoch
