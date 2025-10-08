import cv2
import numpy as np


def smoothing(img):
    """Шаг 1: Сглаживание. Убираем шум с изображения с помощью фильтра Гаусса."""
    # (5, 5) - это размер ядра размытия. Чем он больше, тем сильнее размытие.
    # 1.4 - это стандартное отклонение.
    return cv2.GaussianBlur(img, (5, 5), 1.4)


def compute_gradients(img):
    """Шаг 2: Вычисление градиентов. Находим направление и силу изменения яркости."""
    # Сначала переводим изображение в оттенки серого, так как яркость - это основное.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Оператор Собеля находит, насколько сильно меняется яркость по горизонтали (grad_x)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    # и по вертикали (grad_y).
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # Вычисляем общую силу (магнитуду) градиента в каждом пикселе. Это показывает, насколько "резкой" является граница.
    grad_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
    # Вычисляем направление градиента. Это показывает, в какую сторону "смотрит" граница.
    grad_direction = np.arctan2(grad_y, grad_x)

    return grad_magnitude, grad_direction


def non_maximum_suppression(grad_magnitude, grad_direction):
    """Шаг 3: Подавление немаксимумов. Утончаем "толстые" границы до линий в один пиксель."""
    rows, cols = grad_magnitude.shape
    # Создаем пустое изображение, куда будем складывать "утонченные" границы.
    suppressed = np.zeros((rows, cols), dtype=np.uint8)

    # Переводим направление из радиан в градусы для удобства.
    angle = grad_direction * 180. / np.pi
    angle[angle < 0] += 180

    # Проходим по каждому пикселю (кроме самых крайних).
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            q = 255
            r = 255

            # В зависимости от направления градиента, находим двух соседей,
            # которые лежат вдоль этой линии.
            if (0 <= angle[i, j] < 22.5) or (157.5 <= angle[i, j] <= 180):  # Горизонтальное направление
                q = grad_magnitude[i, j + 1]
                r = grad_magnitude[i, j - 1]
            elif 22.5 <= angle[i, j] < 67.5:  # Диагональ /
                q = grad_magnitude[i + 1, j - 1]
                r = grad_magnitude[i - 1, j + 1]
            elif 67.5 <= angle[i, j] < 112.5:  # Вертикальное направление
                q = grad_magnitude[i + 1, j]
                r = grad_magnitude[i - 1, j]
            elif 112.5 <= angle[i, j] < 157.5:  # Диагональ \
                q = grad_magnitude[i - 1, j - 1]
                r = grad_magnitude[i + 1, j + 1]

            # Если текущий пиксель ярче обоих своих соседей вдоль линии градиента,
            # то он является "пиком" и мы его сохраняем. В противном случае - подавляем (зануляем).
            if (grad_magnitude[i, j] >= q) and (grad_magnitude[i, j] >= r):
                suppressed[i, j] = grad_magnitude[i, j]

    return suppressed


def double_threshold(img, low_ratio=0.05, high_ratio=0.15):
    """Шаг 4: Двойная пороговая фильтрация. Разделяем все пиксели на три категории:
       точные границы, слабые (возможные) границы и точно не границы."""

    # Вычисляем высокий порог как процент от самого яркого пикселя на изображении.
    high_threshold = img.max() * high_ratio
    # Низкий порог вычисляем как процент от высокого.
    low_threshold = high_threshold * low_ratio

    # Создаем пустое изображение для результата.
    res = np.zeros(img.shape, dtype=np.uint8)

    # Задаем "метки" для сильных и слабых пикселей.
    strong = 255  # Сильные границы будут белыми.
    weak = 75     # Слабые - серыми.

    # Находим все пиксели, которые ярче высокого порога - это "сильные" границы.
    strong_i, strong_j = np.where(img >= high_threshold)
    # Находим пиксели между порогами - это "слабые" (кандидаты).
    weak_i, weak_j = np.where((img <= high_threshold) & (img >= low_threshold))

    # Отмечаем их на результирующем изображении.
    res[strong_i, strong_j] = strong
    res[weak_i, weak_j] = weak

    return res, weak, strong


def hysteresis(img, weak, strong=255):
    """Шаг 5: Трассировка границ. Превращаем "слабые" пиксели в "сильные",
       если они соединены с уже существующими сильными границами."""
    rows, cols = img.shape
    # Проходим по всему изображению.
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            # Если находим "слабый" пиксель...
            if img[i, j] == weak:
                # ...проверяем его 8 соседей.
                if np.any(img[i - 1:i + 2, j - 1:j + 2] == strong):
                    # Если хотя бы один из соседей "сильный", то наш пиксель тоже становится частью границы.
                    img[i, j] = strong
                else:
                    # Если он не связан с сильными границами, то это был шум, и мы его удаляем.
                    img[i, j] = 0
    return img


def image_segmentation(img):
    """Основная функция, которая последовательно выполняет все шаги алгоритма Кэнни."""
    # 1. Сглаживание
    img = smoothing(img)

    # 2. Вычисление градиентов
    grad_magnitude, grad_direction = compute_gradients(img)

    # 3. Подавление немаксимумов
    suppressed = non_maximum_suppression(grad_magnitude, grad_direction)

    # 4. Двойная пороговая фильтрация
    thresholded, weak, strong = double_threshold(suppressed)

    # 5. Трассировка границ (гистерезис)
    result = hysteresis(thresholded, weak, strong)

    return result


if __name__ == '__main__':
    img = cv2.imread('../images/cat.jpg')

    result = image_segmentation(img)
    cv2.imwrite('./result_cat.png', result)
