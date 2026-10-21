# Индивидуальная лабораторная работа 1 по дисциплине МРЗвИС вариант 1
# Выполнена студентом группы 321701 БГУИР  Струнец Дмитрий Петрович
# Файл преобразования входного изображения в тип данных принимаемый линейной рециркуляционной сетью
#
# Использованные источники:
# Формальные модели обработки информации и параллельные модели решения задач. Практикум: учебно-методическое пособие / В.П.Ивашенко. – Минск: БГУИР, 2020.

from PIL import Image
import numpy as np


def compute_padding(
    width: int, height: int, block_w: int, block_h: int
) -> tuple[int, int]:
    pad_w = (block_w - (width % block_w)) % block_w
    pad_h = (block_h - (height % block_h)) % block_h
    return pad_w, pad_h


def pad_reflection(img_arr: np.ndarray, pad_w: int, pad_h: int) -> np.ndarray:
    if pad_w == 0 and pad_h == 0:
        return img_arr.copy()
    pad_top = pad_left = 0
    pad_bottom = pad_h
    pad_right = pad_w
    padded = np.pad(
        img_arr, ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)), mode="reflect"
    )
    return padded


def normalize_pixel_values(
    arr: np.ndarray, value_range: tuple[float, float] = (-1.0, 1.0)
) -> np.ndarray:
    min_r, max_r = value_range
    arr_f = arr.astype(np.float32) / 255.0
    scaled = arr_f * (max_r - min_r) + min_r
    return scaled


def denormalize_pixel_values(
    arr: np.ndarray, value_range: tuple[float, float] = (-1.0, 1.0)
) -> np.ndarray:
    min_r, max_r = value_range
    unscaled = (arr - min_r) / (max_r - min_r)
    unscaled = np.clip(unscaled, 0.0, 1.0)
    return (unscaled * 255.0).round().astype(np.uint8)


def split_into_blocks(
    img: Image.Image,
    block_w: int,
    block_h: int,
    value_range: tuple[float, float] = (-1.0, 1.0),
) -> tuple[np.ndarray, int, int, int, int]:
    if img.mode != "RGB":
        img = img.convert("RGB")

    arr = np.array(img)
    H, W = arr.shape[:2]
    pad_w, pad_h = compute_padding(W, H, block_w, block_h)
    padded = pad_reflection(arr, pad_w, pad_h)
    H_p, W_p = padded.shape[:2]

    blocks = []
    for y in range(0, H_p, block_h):
        for x in range(0, W_p, block_w):
            patch = padded[y : y + block_h, x : x + block_w, :]
            assert (
                patch.shape[0] == block_h and patch.shape[1] == block_w
            ), "Patch size wrong after padding"
            norm = normalize_pixel_values(patch, value_range).astype(np.float32)
            blocks.append(norm.reshape(-1))
    blocks_arr = np.stack(blocks, axis=0)
    return blocks_arr, W, H, W_p, H_p


def reconstruct_image_from_blocks(
    blocks: np.ndarray,
    original_width: int,
    original_height: int,
    block_w: int,
    block_h: int,
    padded_width: int,
    padded_height: int,
    value_range: tuple[float, float] = (-1.0, 1.0),
) -> Image.Image:
    canvas = np.zeros((padded_height, padded_width, 3), dtype=np.float32)

    blocks_per_row = padded_width // block_w
    for idx in range(blocks.shape[0]):
        row = idx // blocks_per_row
        col = idx % blocks_per_row
        y = row * block_h
        x = col * block_w
        flat = blocks[idx]
        patch = flat.reshape((block_h, block_w, 3))
        canvas[y : y + block_h, x : x + block_w, :] = patch

    denorm = denormalize_pixel_values(canvas, value_range)
    cropped = denorm[:original_height, :original_width, :]
    return Image.fromarray(cropped, mode="RGB")
