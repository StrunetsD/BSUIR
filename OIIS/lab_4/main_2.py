
import numpy as np
from PIL import Image, ImageFilter
import time
import networkx as nx

def color_difference(pixel1, pixel2):
    """Вычисление цветовой разницы между пикселями"""
    return np.sqrt(np.sum((np.array(pixel1) - np.array(pixel2)) ** 2))

def build_edges(image, use_8_neighbors=False):
    """Построение ребер графа между соседними пикселями"""
    height, width = image.shape[:2]
    edges = []

    for y in range(height):
        for x in range(width):
            current_idx = y * width + x
            current_pixel = image[y, x]

            # Правый сосед
            if x < width - 1:
                right_idx = y * width + (x + 1)
                weight = color_difference(current_pixel, image[y, x + 1])
                edges.append((current_idx, right_idx, weight))

            # Нижний сосед
            if y < height - 1:
                bottom_idx = (y + 1) * width + x
                weight = color_difference(current_pixel, image[y + 1, x])
                edges.append((current_idx, bottom_idx, weight))

            # Диагональные соседи (только для 8-связности)
            if use_8_neighbors:
                if x < width - 1 and y < height - 1:
                    diag_idx = (y + 1) * width + (x + 1)
                    weight = color_difference(current_pixel, image[y + 1, x + 1])
                    edges.append((current_idx, diag_idx, weight))

                if x > 0 and y < height - 1:
                    diag_idx = (y + 1) * width + (x - 1)
                    weight = color_difference(current_pixel, image[y + 1, x - 1])
                    edges.append((current_idx, diag_idx, weight))

    return edges

def segment_image(image_path, sigma=1.0, K=10.0, min_size=2000, use_8_neighbors=True):
    """Основная функция сегментации"""
    start_time = time.time()

    # Загрузка и предобработка изображения
    image = Image.open(image_path)
    print(f"Изображение: {image.size}, режим: {image.mode}")

    # Размытие по Гауссу
    smoothed = image.filter(ImageFilter.GaussianBlur(sigma))
    image_array = np.array(smoothed)
    height, width = image_array.shape[:2]
    total_pixels = height * width

    # Построение графа
    print("Строим граф...")
    edges = build_edges(image_array, use_8_neighbors)

    # Сортировка ребер по весу (разнице цветов)
    edges.sort(key=lambda x: x[2])

    # Инициализация системы множеств с помощью networkx
    dset = nx.utils.union_find.UnionFind(range(total_pixels))
    threshold = [K] * total_pixels
    size = [1] * total_pixels  # Размер компонент

    # Объединение регионов
    print("Объединяем регионы...")
    for edge in edges:
        a, b, weight = edge
        root_a, root_b = dset[a], dset[b]

        if root_a != root_b and weight <= min(threshold[root_a], threshold[root_b]):
            dset.union(a, b)
            new_root = dset[a]
            size[new_root] = size[root_a] + size[root_b]
            threshold[new_root] = weight + (K / size[new_root])

    # Удаление маленьких компонент
    print("Удаляем маленькие компоненты...")
    for edge in edges:
        a, b, _ = edge
        root_a, root_b = dset[a], dset[b]

        if root_a != root_b and (size[root_a] < min_size or size[root_b] < min_size):
            dset.union(a, b)
            new_root = dset[a]
            size[new_root] = size[root_a] + size[root_b]
            threshold[new_root] = min(threshold[root_a], threshold[root_b])

    # Визуализация результата
    print("Создаем сегментированное изображение...")
    segmented = Image.new('RGB', (width, height))
    pixels = segmented.load()

    # Случайные цвета для каждого сегмента
    colors = {}
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            segment_id = dset[idx]

            if segment_id not in colors:
                colors[segment_id] = (
                    np.random.randint(0, 255),
                    np.random.randint(0, 255),
                    np.random.randint(0, 255)
                )

            pixels[x, y] = colors[segment_id]

    # Подсчет количества сегментов
    num_sets = len(set(dset[parent] for parent in range(total_pixels)))
    print(f"Количество сегментов: {num_sets}")
    print(f"Время выполнения: {time.time() - start_time:.2f} секунд")

    return segmented

# Пример использования
if __name__ == "__main__":
    result = segment_image(
        image_path="../images/cat_3.jpg",
        sigma=1.0,  # Сила размытия
        K=10.0,  # Параметр чувствительности
        min_size=2000,  # Минимальный размер сегмента
        use_8_neighbors=True  # Использовать 8-связность
    )
    result.save("./result_cat_2.png")
    result.show()
