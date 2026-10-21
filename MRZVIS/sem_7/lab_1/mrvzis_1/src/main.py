# Индивидуальная лабораторная работа 1 по дисциплине МРЗвИС вариант 1
# Выполнена студентом группы 321701 БГУИР  Струнец Дмитрий Петрович
# Файл начала программы, создающий линейную рециркуляционную сеть и сохраняющий результат выполнения программы
#
# Использованные источники:
# Формальные модели обработки информации и параллельные модели решения задач. Практикум: учебно-методическое пособие / В.П.Ивашенко. – Минск: БГУИР, 2020.

import os
import time

import numpy as np
from PIL import Image

from network import Network
from image_processing import (
    reconstruct_image_from_blocks,
    split_into_blocks,
)
from arguments_parser import parse


def main() -> None:
    args = parse()
    if args.seed is not None:
        np.random.seed(args.seed)

    m, n = args.m, args.n
    img = Image.open(args.input)
    blocks, orig_w, orig_h, padded_w, padded_h = split_into_blocks(img, m, n)

    input_size = blocks.shape[1]
    secret_size = (
        args.secret_layer if args.secret_layer is not None else input_size // 10
    )
    compress_coef = (8 * blocks.shape[0] * blocks.shape[1]) / (
        32 * 2 + (blocks.shape[1] + blocks.shape[0]) * secret_size * 64
    )

    print(f"Compress coefficient: {compress_coef:.4f}")
    if compress_coef <= 1:
        print("The compress coefficient isn't greater than 1")
        return

    net = Network(
        input_size,
        secret_size,
        learning_rate=args.lr,
        max_error=args.max_error,
        max_epoch=args.max_epoch,
    )
    start_time = time.time()
    net.train_network(blocks)
    end_time = time.time()
    print(f"Training took {end_time - start_time:.2f} seconds")

    recon_blocks = (blocks @ net.W1) @ net.W2

    recon_img = reconstruct_image_from_blocks(
        recon_blocks,
        orig_w,
        orig_h,
        m,
        n,
        padded_w,
        padded_h,
    )

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    recon_img.save(args.output)
    recon_img.show()


if __name__ == "__main__":
    main()
