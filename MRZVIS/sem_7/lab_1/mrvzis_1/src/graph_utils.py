# Индивидуальная лабораторная работа 1 по дисциплине МРЗвИС вариант 1
# Выполнена студентом группы 321701 БГУИР  Струнец Дмитрий Петрович
# Файл-утилита для генерации графиков и таблиц
#
# Использованные источники:
# Формальные модели обработки информации и параллельные модели решения задач. Практикум: учебно-методическое пособие / В.П.Ивашенко. – Минск: БГУИР, 2020.

import os
import numpy as np
import matplotlib.pyplot as plt
from network import Network
from typing import List, Tuple, Callable, Any

MAX_EPOCH = 100000
GRAPHS_DIR = os.path.join("results", "graphs")
TABLES_DIR = os.path.join("results", "tables")


def run_sweep_and_collect(
    pixel_blocks: np.ndarray,
    values: list,
    get_params: Callable[[Any], Tuple[float, float, int]],
    get_x_value: Callable[[Any, int], float],
) -> Tuple[List[int], List[float]]:
    """
    Runs network training over a range of values and collects results.

    Args:
        pixel_blocks: The input data for the network.
        values: A list of parameter values to iterate over.
        get_params: A function that takes a value and returns (lr, max_error, secret_size).
        get_x_value: A function that takes a value and secret_size and returns the corresponding x-axis value.

    Returns:
        A tuple containing a list of iteration counts and a list of x-axis values.
    """
    iters_vec = []
    x_values = []
    input_size = pixel_blocks.shape[1]

    for val in values:
        lr, max_error, secret_size = get_params(val)
        x_record = get_x_value(val, secret_size)

        print(
            f"Training with lr={lr}, max_error={max_error}, secret_size={secret_size}, x_record={x_record}"
        )

        net = Network(
            input_size=input_size,
            output_size=secret_size,
            learning_rate=lr,
            max_error=max_error,
            max_epoch=MAX_EPOCH,
        )

        iters_done = net.train_network(pixel_blocks)

        iters_vec.append(iters_done)
        x_values.append(x_record)
        print(f"→ Completed in {iters_done} epochs.")

    return iters_vec, x_values


def plot_graph(
    iters: List[int],
    data: List[float],
    caption: str,
    axis_label: str,
    filename: str,
):
    """Plots and saves a single graph."""
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    path = os.path.join(GRAPHS_DIR, filename)
    plt.figure(figsize=(12, 8))
    plt.plot(data, iters, marker="o", linestyle="-", color="royalblue")
    plt.title(caption, fontsize=16)
    plt.xlabel(axis_label, fontsize=12)
    plt.ylabel("Кол-во итераций", fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"→ Graph saved to '{path}'")


def plot_graph_multi(
    all_iters: List[List[int]],
    all_x_values: List[List[float]],
    labels: List[str],
    colors: List[str],
    data_name: str,
    axis_label: str,
    filename: str,
):
    """Plots and saves a graph with multiple lines."""
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    path = os.path.join(GRAPHS_DIR, filename)
    plt.figure(figsize=(12, 8))
    for iters, x_vals, label, color in zip(all_iters, all_x_values, labels, colors):
        plt.plot(x_vals, iters, marker="o", linestyle="-", color=color, label=label)

    plt.title(f"Зависимость количества итераций от {data_name}", fontsize=16)
    plt.xlabel(axis_label, fontsize=12)
    plt.ylabel("Кол-во итераций", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"→ Graph saved to '{path}'")


def print_table(
    title: str,
    fig_number: int,
    column_label: str,
    param_values: List[float],
    iterations: List[int],
    save_to_file: bool = True,
):
    """Prints a formatted table to the console and optionally saves it to a file."""
    header = f"{title} (рис. {fig_number})"
    table_lines = [
        header,
        f"{'Наблюдение':<12} {'Кол-во итераций':<20} {column_label}",
    ]
    for i, (iters, param) in enumerate(zip(iterations, param_values)):
        table_lines.append(f"{i + 1:<12} {iters:<20} {param:.6f}")

    # Print to console
    print("\n" + "\n".join(table_lines) + "\n")

    if save_to_file:
        os.makedirs(TABLES_DIR, exist_ok=True)
        path = os.path.join(TABLES_DIR, f"table_{fig_number}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(table_lines))
        print(f"→ Table saved to '{path}'")
