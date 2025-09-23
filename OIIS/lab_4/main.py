import cv2
import numpy as np
import os

# Папка с исходными изображениями
input_folder = 'images_laba4'

# Папка для сохранения результатов
output_folder = 'result_images_laba4'

# Создаем папку для результатов, если она не существует
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Перебираем все файлы в папке с исходными изображениями
for filename in os.listdir(input_folder):
    if filename.endswith('.jpg'):
        # Загрузка изображения
        img = cv2.imread(os.path.join(input_folder, filename))

        # алгоритм Кэнни
        # Вычисление градиента
        # Gray = 0.299 * R + 0.587 * G + 0.114 * B
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # один цветовой канал
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        # [1  0  -1]
        # [2  0  -2]
        # [1  0  -1]

        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        # [1   2  1]
        # [0   0  0]
        # [-1 -2 -1]

        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Сохранение результата
        output_filename = os.path.splitext(filename)[0] + '_result_grey.jpg'
        output_path = os.path.join(output_folder, output_filename)
        cv2.imwrite(output_path, grad_magnitude)

        # Бинаризация изображения градиента
        _, binary_image = cv2.threshold(np.uint8(grad_magnitude),
                                        100,
                                        255,
                                        cv2.THRESH_BINARY)  # бинарная (черно-белая) пороговая обработка
        output_filename = os.path.splitext(filename)[0] + '_result_binary.jpg'
        output_path = os.path.join(output_folder, output_filename)
        cv2.imwrite(output_path, binary_image)

        # Подавление немаксимумов
        non_max_suppressed = np.zeros(binary_image.shape, dtype=np.uint8)
        for i in range(1, binary_image.shape[0] - 1):
            for j in range(1, binary_image.shape[1] - 1):
                if binary_image[i, j] == 255:
                    dx = grad_x[i, j]
                    dy = grad_y[i, j]
                    magnitude = grad_magnitude[i, j]
                    if (dx != 0) or (dy != 0):
                        angle = np.arctan2(dy, dx)
                        angle_deg = angle * 180. / np.pi

                        if 0 <= angle_deg < 22.5 or 157.5 <= angle_deg <= 180:
                            # Горизонтальное направление
                            if (magnitude >= grad_magnitude[i, j - 1]) and (magnitude >= grad_magnitude[i, j + 1]):
                                non_max_suppressed[i, j] = magnitude
                        elif 22.5 <= angle_deg < 67.5:
                            # Диагональное 1 (верхний левый - нижний правый)
                            if (magnitude >= grad_magnitude[i - 1, j - 1]) and (
                                    magnitude >= grad_magnitude[i + 1, j + 1]):
                                non_max_suppressed[i, j] = magnitude
                        elif 67.5 <= angle_deg < 112.5:
                            # Вертикальное направление
                            if (magnitude >= grad_magnitude[i - 1, j]) and (magnitude >= grad_magnitude[i + 1, j]):
                                non_max_suppressed[i, j] = magnitude
                        else:
                            # Диагональное 2 (верхний правый - нижний левый)
                            if (magnitude >= grad_magnitude[i - 1, j + 1]) and (
                                    magnitude >= grad_magnitude[i + 1, j - 1]):
                                non_max_suppressed[i, j] = magnitude

        # Сохранение результата
        output_filename = os.path.splitext(filename)[0] + '_result.jpg'
        output_path = os.path.join(output_folder, output_filename)
        cv2.imwrite(output_path, non_max_suppressed)