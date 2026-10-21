# Индивидуальная лабораторная работа 1 по дисциплине МРЗвИС вариант 1
# Выполнена студентом группы 321701 БГУИР  Струнец Дмитрий Петрович
# Файл для генерации графиков производительности сети
#
# Использованные источники:
# Формальные модели обработки информации и параллельные модели решения задач. Практикум: учебно-методическое пособие / В.П.Ивашенко. – Минск: БГУИР, 2020.

from PIL import Image
import numpy as np
from image_processing import split_into_blocks
from graph_utils import (
    run_sweep_and_collect,
    plot_graph,
    plot_graph_multi,
    print_table,
)


def plot(input_image_path: str):
    """
    Генерирует графики производительности сети.
    Для графиков по нескольким изображениям ожидаются файлы pictures/1.bmp, 2.bmp, 3.bmp.
    """
    try:
        img = Image.open(input_image_path)
    except FileNotFoundError:
        print(f"Error: Input image '{input_image_path}' not found for graphing.")
        return

    block_m, block_n = 8, 8
    pixel_blocks, *_ = split_into_blocks(img, block_m, block_n)

    error_limits = [
        4000.0,
        5000.0,
        7500.0,
        10000.0,
        12500.0,
        15000.0,
        17500.0,
        20000.0,
        22500.0,
    ]

    print("\n--- Generating Compression Ratio Graphs (Multi-Run) ---")
    compress_graph_multi(pixel_blocks)
    #
    # print("\n--- Generating Learning Rate Graph ---")
    # learning_rate_graph(pixel_blocks)

    # print("\n--- Generating Max Error Graph ---")
    # error_graph(pixel_blocks, error_limits)

    # print("\n--- Generating Combined Max Error Graph for Multiple Images ---")
    # multi_error_graphs((block_m, block_n), error_limits)


def multi_error_graphs(block_size: tuple[int, int], error_limits: list[float]):
    files = ["1.bmp", "2.bmp", "3.bmp"]
    colors = ["red", "green", "royalblue"]
    all_iters = []
    all_x_values = []
    labels = []

    for i, filename in enumerate(files):
        try:
            img = Image.open(f"pictures/{filename}")
            print(f"Processing image: {filename}")
        except FileNotFoundError:
            print(
                f"Warning: Skipping '{filename}' for multi-error graph, file not found."
            )
            continue

        pixel_blocks, *_ = split_into_blocks(img, block_size[0], block_size[1])
        iters, x_vals = run_sweep_and_collect(
            pixel_blocks,
            error_limits,
            lambda me: (0.0002, me, 15),
            lambda val, _: val,
        )
        print_table(
            f"Изображение {i+1} ({filename})",
            i + 4,
            "e",
            error_limits,
            iters,
            save_to_file=True,
        )
        all_iters.append(iters)
        all_x_values.append(x_vals)
        labels.append(f"Изображение {i + 1}")

    if not all_iters:
        print("No images processed for multi-error graph. Aborting plot.")
        return

    plot_graph_multi(
        all_iters,
        all_x_values,
        labels,
        colors,
        "максимально допустимой ошибки",
        "Максимально допустимая ошибка",
        "combined_plot.png",
    )


def error_graph(pixel_blocks: np.ndarray, error_limits: list[float]):

    error_iters, _ = run_sweep_and_collect(
        pixel_blocks,
        error_limits,
        lambda me: (0.0002, me, 15),
        lambda val, _: val,
    )
    plot_graph(
        error_iters,
        error_limits,
        "Зависимость количества итераций от максимально допустимой ошибки",
        "Максимально допустимая ошибка",
        "max_error.png",
    )
    print_table(
        "Зависимость количества итераций от максимально допустимой ошибки",
        2,
        "e",
        error_limits,
        error_iters,
        save_to_file=True,
    )


def compress_graph_multi(pixel_blocks: np.ndarray):
    NUM_RUNS = 10
    secret_layer_sizes = [5, 8, 11, 14, 17, 21]
    # secret_layer_sizes = [22]
    q = pixel_blocks.shape[0]
    n_in = pixel_blocks.shape[1]

    all_iters = [[] for _ in secret_layer_sizes]
    comp_coefs = []

    for run_idx in range(NUM_RUNS):
        print(f"Starting run {run_idx + 1}/{NUM_RUNS}...")
        np.random.seed(1000 + 100 * run_idx)
        iters_vec, current_comp_coefs = run_sweep_and_collect(
            pixel_blocks,
            secret_layer_sizes,
            lambda out_size: (0.0002, 5000.0, out_size),
            lambda _, output_size: (8.0 * q * n_in)
            / (32.0 * 2.0 + (n_in + q) * output_size * 64.0),
        )
        if not comp_coefs:
            comp_coefs = current_comp_coefs
        for i, iters in enumerate(iters_vec):
            all_iters[i].append(iters)

    avg_iters = [
        round(sum(run_results) / len(run_results)) for run_results in all_iters
    ]

    plot_graph(
        avg_iters,
        comp_coefs,
        "Зависимость среднего количества итераций от коэффициента сжатия",
        "Коэффициент сжатия",
        "compress_avg.png",
    )

    print_table("Среднее количество итераций", 11, "Z", comp_coefs, avg_iters)


def compress_graph(pixel_blocks: np.ndarray):
    secret_layer_sizes = [10, 15, 20, 25, 30, 35, 48]
    q = pixel_blocks.shape[0]
    n_in = pixel_blocks.shape[1]

    compress_iters, comp_coefs = run_sweep_and_collect(
        pixel_blocks,
        secret_layer_sizes,
        lambda out_size: (0.00035, 5000.0, out_size),
        lambda _, output_size: (8.0 * q * n_in)
        / (32.0 * 2.0 + (n_in + q) * output_size * 32.0),
    )

    plot_graph(
        compress_iters,
        comp_coefs,
        "Зависимость количества итераций от коэффициента сжатия",
        "Коэффициент сжатия",
        "compress.png",
    )
    print_table(
        "Зависимость количества итераций от коэффициента сжатия",
        3,
        "Z",
        comp_coefs,
        compress_iters,
        save_to_file=True,
    )


def learning_rate_graph(pixel_blocks: np.ndarray):
    lr_values = [0.00008, 0.0001, 0.00013, 0.00015, 0.00018, 0.0002, 0.00023, 0.00025]
    lr_iters, _ = run_sweep_and_collect(
        pixel_blocks,
        lr_values,
        lambda lr: (lr, 5000.0, 15),
        lambda val, _: val,
    )
    plot_graph(
        lr_iters,
        lr_values,
        "Зависимость количества итераций от коэффициента обучения",
        "Коэффициент обучения",
        "learning_rate.png",
    )
    print_table(
        "Зависимость количества итераций от коэффициента обучения",
        1,
        "lr",
        lr_values,
        lr_iters,
        save_to_file=True,
    )
