import gradio as gr              # Библиотека для создания веб-интерфейса
import cv2                       # OpenCV для обработки изображений (рисование, размытие и т.д.)
import numpy as np               # Для работы с массивами и математикой
from ultralytics import YOLO     # Сама нейросеть YOLO для детекции объектов
from PIL import Image, ImageDraw # Для работы с изображениями в других форматах
import torch                     # PyTorch - для работы с GPU (если есть)
from pathlib import Path         
from typing import List, Tuple, Optional, Dict  



class MapObjectDetectorYOLO:
    """Детектор объектов на картах с использованием YOLO"""

    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Инициализация детектора

        Args:
            model_path: путь к модели YOLO (или название предобученной модели)
        """
        print(f"Загрузка модели YOLO: {model_path}")
        self.model = YOLO(model_path)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Используется устройство: {self.device}")

        # Предопределенные цвета для разных классов
        self.colors = self._generate_colors(80)

        # Кэш для последних детекций
        self.last_results = None
        self.last_image = None

    def _generate_colors(self, n: int) -> List[Tuple[int, int, int]]:
        """Генерация уникальных цветов для классов"""
        np.random.seed(42)
        colors = []
        for i in range(n):
            colors.append(tuple(np.random.randint(0, 255, 3).tolist()))
        return colors

    def detect_objects(self,
                       image: np.ndarray,
                       confidence: float = 0.25,
                       iou_threshold: float = 0.45,
                       classes: Optional[List[int]] = None) -> Tuple[np.ndarray, Dict]:
        """
        Детекция объектов на изображении

        Args:
            image: входное изображение (numpy array)
            confidence: порог уверенности (0-1)
            iou_threshold: порог IoU для NMS
            classes: список ID классов для детекции (None = все классы)

        Returns:
            (изображение с детекциями, статистика)
        """
        # Конвертируем PIL Image в numpy если нужно
        if isinstance(image, Image.Image):
            image = np.array(image)

        # Сохраняем для возможной замены объектов
        self.last_image = image.copy()

        # Запускаем детекцию
        results = self.model.predict(
            image,
            conf=confidence,
            iou=iou_threshold,
            classes=classes,
            device=self.device,
            verbose=False
        )

        # Сохраняем результаты
        self.last_results = results[0]

        # Получаем результаты
        annotated_image = results[0].plot()

        # Собираем статистику
        stats = self._collect_statistics(results[0])

        return annotated_image, stats

    def _collect_statistics(self, result) -> Dict:
        """Сбор статистики по детекциям"""
        boxes = result.boxes

        if len(boxes) == 0:
            return {
                "total_objects": 0,
                "classes": {},
                "confidence_avg": 0.0
            }

        # Подсчет объектов по классам
        class_counts = {}
        confidences = []

        for box in boxes:
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = float(box.conf[0])

            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            confidences.append(conf)

        stats = {
            "total_objects": len(boxes),
            "classes": class_counts,
            "confidence_avg": np.mean(confidences) if confidences else 0.0,
            "confidence_min": np.min(confidences) if confidences else 0.0,
            "confidence_max": np.max(confidences) if confidences else 0.0
        }

        return stats

    def detect_specific_class(self,
                              image: np.ndarray,
                              target_class: str,
                              confidence: float = 0.25) -> Tuple[np.ndarray, int]:
        """
        Детекция объектов определенного класса

        Args:
            image: входное изображение
            target_class: название класса для поиска
            confidence: порог уверенности

        Returns:
            (изображение с детекциями, количество найденных объектов)
        """
        # Находим ID класса
        class_id = None
        for idx, name in self.model.names.items():
            if name.lower() == target_class.lower():
                class_id = idx
                break

        if class_id is None:
            raise ValueError(f"Класс '{target_class}' не найден в модели")

        # Детекция только этого класса
        annotated_image, stats = self.detect_objects(
            image,
            confidence=confidence,
            classes=[class_id]
        )

        count = stats['classes'].get(target_class, 0)

        return annotated_image, count

    def replace_objects(self,
                        source_class: str,
                        replacement_type: str = "cube",
                        replacement_image: Optional[np.ndarray] = None,
                        inpaint_background: bool = True) -> Tuple[np.ndarray, str]:
        """
        Замена объектов на изображении

        Args:
            source_class: класс объектов для замены
            replacement_type: тип замены ("cube", "sphere", "custom", "blur", "remove")
            replacement_image: пользовательское изображение для замены
            inpaint_background: заполнять ли фон при удалении

        Returns:
            (измененное изображение, отчет)
        """
        if self.last_results is None or self.last_image is None:
            raise ValueError("Сначала выполните детекцию объектов!")

        # Находим ID класса
        class_id = None
        for idx, name in self.model.names.items():
            if name.lower() == source_class.lower():
                class_id = idx
                break

        if class_id is None:
            raise ValueError(f"Класс '{source_class}' не найден")

        # Копируем изображение
        result_image = self.last_image.copy()
        replaced_count = 0

        # Получаем все боксы нужного класса
        boxes = self.last_results.boxes

        for box in boxes:
            if int(box.cls[0]) == class_id:
                # Получаем координаты
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Удаляем старый объект (заполняем фон)
                if inpaint_background:
                    result_image = self._inpaint_region(result_image, x1, y1, x2, y2)

                # Добавляем новый объект
                if replacement_type == "cube":
                    result_image = self._draw_cube(result_image, x1, y1, x2, y2)
                elif replacement_type == "sphere":
                    result_image = self._draw_sphere(result_image, x1, y1, x2, y2)
                elif replacement_type == "blur":
                    result_image = self._blur_region(result_image, x1, y1, x2, y2)
                elif replacement_type == "remove":
                    pass  # Уже удалили при инпейнте
                elif replacement_type == "custom" and replacement_image is not None:
                    result_image = self._overlay_image(result_image, replacement_image, x1, y1, x2, y2)

                replaced_count += 1

        report = f"✅ Заменено объектов '{source_class}': {replaced_count}"

        return result_image, report

    def _inpaint_region(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        """Заполнение региона с помощью инпейнтинга"""
        # Создаем маску
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255

        # Применяем инпейнтинг
        result = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

        return result

    def _blur_region(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        """Размытие региона"""
        roi = image[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(roi, (51, 51), 0)
        result = image.copy()
        result[y1:y2, x1:x2] = blurred
        return result

    def _draw_cube(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        """Рисует 3D куб"""
        result = image.copy()

        # Размеры куба
        width = x2 - x1
        height = y2 - y1
        size = min(width, height)

        # Центр
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # Параметры 3D куба
        cube_size = int(size * 0.8)
        depth = cube_size // 3

        # Вершины куба
        # Передняя грань
        front_tl = (cx - cube_size // 2, cy - cube_size // 2)
        front_tr = (cx + cube_size // 2, cy - cube_size // 2)
        front_bl = (cx - cube_size // 2, cy + cube_size // 2)
        front_br = (cx + cube_size // 2, cy + cube_size // 2)

        # Задняя грань (смещенная для 3D эффекта)
        back_tl = (front_tl[0] - depth, front_tl[1] - depth)
        back_tr = (front_tr[0] - depth, front_tr[1] - depth)
        back_bl = (front_bl[0] - depth, front_bl[1] + depth // 2)
        back_br = (front_br[0] - depth, front_br[1] + depth // 2)

        # Цвета граней
        color_front = (70, 130, 180)  # Синий
        color_top = (100, 160, 210)  # Светлее
        color_side = (40, 100, 150)  # Темнее

        # Рисуем грани
        # Верхняя грань
        pts_top = np.array([back_tl, back_tr, front_tr, front_tl], np.int32)
        cv2.fillPoly(result, [pts_top], color_top)
        cv2.polylines(result, [pts_top], True, (0, 0, 0), 2)

        # Боковая грань
        pts_side = np.array([back_tr, back_br, front_br, front_tr], np.int32)
        cv2.fillPoly(result, [pts_side], color_side)
        cv2.polylines(result, [pts_side], True, (0, 0, 0), 2)

        # Передняя грань
        pts_front = np.array([front_tl, front_tr, front_br, front_bl], np.int32)
        cv2.fillPoly(result, [pts_front], color_front)
        cv2.polylines(result, [pts_front], True, (0, 0, 0), 2)

        return result

    def _draw_sphere(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        """Рисует 3D сферу с градиентом"""
        result = image.copy()

        # Размеры
        width = x2 - x1
        height = y2 - y1
        radius = min(width, height) // 2

        # Центр
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # Создаем маску для сферы
        y_coords, x_coords = np.ogrid[:image.shape[0], :image.shape[1]]
        mask = ((x_coords - cx) ** 2 + (y_coords - cy) ** 2) <= radius ** 2

        # Создаем градиент для 3D эффекта
        light_x, light_y = cx - radius // 3, cy - radius // 3

        sphere_layer = np.zeros_like(image)

        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                if mask[i, j]:
                    # Расстояние от точки до центра
                    dist_center = np.sqrt((j - cx) ** 2 + (i - cy) ** 2)
                    # Расстояние от точки до источника света
                    dist_light = np.sqrt((j - light_x) ** 2 + (i - light_y) ** 2)

                    # Интенсивность освещения
                    intensity = 1 - (dist_center / radius) * 0.7
                    light_factor = 1 - (dist_light / (radius * 1.5))
                    light_factor = max(0, min(1, light_factor))

                    final_intensity = intensity * (0.5 + light_factor * 0.5)

                    # Цвет (красная сфера)
                    color = np.array([50, 50, 200]) * final_intensity
                    sphere_layer[i, j] = color.astype(np.uint8)

        # Накладываем сферу
        result[mask] = sphere_layer[mask]

        # Рисуем контур
        cv2.circle(result, (cx, cy), radius, (0, 0, 0), 2)

        # Добавляем блик
        highlight_radius = radius // 4
        cv2.circle(result, (light_x, light_y), highlight_radius, (255, 255, 255), -1)

        return result

    def _overlay_image(self, background: np.ndarray, overlay: np.ndarray,
                       x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        """Накладывает пользовательское изображение"""
        result = background.copy()

        # Конвертируем overlay в нужный формат
        if isinstance(overlay, Image.Image):
            overlay = np.array(overlay)

        # Изменяем размер overlay под бокс
        width = x2 - x1
        height = y2 - y1

        overlay_resized = cv2.resize(overlay, (width, height))

        # Если есть альфа-канал
        if overlay_resized.shape[2] == 4:
            alpha = overlay_resized[:, :, 3] / 255.0
            for c in range(3):
                result[y1:y2, x1:x2, c] = (
                        alpha * overlay_resized[:, :, c] +
                        (1 - alpha) * result[y1:y2, x1:x2, c]
                )
        else:
            result[y1:y2, x1:x2] = overlay_resized

        return result


# Глобальный детектор
detector = None


def initialize_detector(model_choice: str) -> str:
    """Инициализация модели"""
    global detector

    model_map = {
        "YOLOv8 Nano (быстрая)": "yolov8n.pt",
        "YOLOv8 Small": "yolov8s.pt",
        "YOLOv8 Medium": "yolov8m.pt",
        "YOLOv8 Large (точная)": "yolov8l.pt"
    }

    model_path = model_map.get(model_choice, "yolov8n.pt")

    try:
        detector = MapObjectDetectorYOLO(model_path)
        return f"✅ Модель {model_choice} успешно загружена!"
    except Exception as e:
        return f"❌ Ошибка загрузки модели: {str(e)}"


def detect_all_objects(image, confidence, iou_threshold):
    """Детекция всех объектов"""
    global detector

    if detector is None:
        return None, "⚠️ Сначала загрузите модель!"

    if image is None:
        return None, "⚠️ Загрузите изображение!"

    try:
        annotated_image, stats = detector.detect_objects(
            image,
            confidence=confidence,
            iou_threshold=iou_threshold
        )

        # Формируем текстовый отчет
        report = f"""
📊 **Результаты детекции:**
- Всего объектов найдено: **{stats['total_objects']}**
- Средняя уверенность: **{stats['confidence_avg']:.2%}**
- Мин/Макс уверенность: **{stats['confidence_min']:.2%}** / **{stats['confidence_max']:.2%}**

📋 **Найденные классы:**
"""
        for cls_name, count in sorted(stats['classes'].items(), key=lambda x: x[1], reverse=True):
            report += f"\n- {cls_name}: **{count}** шт."

        return annotated_image, report

    except Exception as e:
        return None, f"❌ Ошибка детекции: {str(e)}"


def detect_specific(image, target_class, confidence):
    """Детекция конкретного класса объектов"""
    global detector

    if detector is None:
        return None, "⚠️ Сначала загрузите модель!"

    if image is None:
        return None, "⚠️ Загрузите изображение!"

    if not target_class:
        return None, "⚠️ Укажите класс для поиска!"

    try:
        annotated_image, count = detector.detect_specific_class(
            image,
            target_class,
            confidence=confidence
        )

        report = f"""
🎯 **Поиск объектов класса: {target_class}**

Найдено объектов: **{count}** шт.
"""

        return annotated_image, report

    except ValueError as e:
        available_classes = ", ".join(list(detector.model.names.values())[:20])
        return None, f"❌ {str(e)}\n\nДоступные классы: {available_classes}..."
    except Exception as e:
        return None, f"❌ Ошибка: {str(e)}"


def replace_objects_on_image(image, source_class, replacement_type, custom_image,
                             confidence, use_inpaint):
    """Замена объектов на изображении"""
    global detector

    if detector is None:
        return None, "⚠️ Сначала загрузите модель!"

    if image is None:
        return None, "⚠️ Загрузите изображение!"

    if not source_class:
        return None, "⚠️ Укажите класс объектов для замены!"

    try:
        # Сначала детектируем объекты
        detector.detect_objects(image, confidence=confidence)

        # Заменяем объекты
        result_image, report = detector.replace_objects(
            source_class=source_class,
            replacement_type=replacement_type,
            replacement_image=custom_image,
            inpaint_background=use_inpaint
        )

        full_report = f"""
🔄 **Замена объектов**

{report}

Тип замены: **{replacement_type}**
Класс: **{source_class}**
"""

        return result_image, full_report

    except ValueError as e:
        available_classes = ", ".join(list(detector.model.names.values())[:20])
        return None, f"❌ {str(e)}\n\nДоступные классы: {available_classes}..."
    except Exception as e:
        return None, f"❌ Ошибка: {str(e)}"


def get_available_classes():
    """Получение списка доступных классов"""
    global detector

    if detector is None:
        return "⚠️ Сначала загрузите модель!"

    classes = list(detector.model.names.values())

    result = "🏷️ **Доступные классы для детекции:**\n\n"

    # Группируем по категориям для удобства
    categories = {
        "Транспорт": ["car", "truck", "bus", "motorcycle", "bicycle", "train", "boat", "airplane"],
        "Люди и животные": ["person", "cat", "dog", "horse", "sheep", "cow", "bird"],
        "Объекты на улице": ["traffic light", "fire hydrant", "stop sign", "parking meter", "bench"],
        "Мебель и интерьер": ["chair", "couch", "bed", "dining table", "toilet"],
        "Электроника": ["tv", "laptop", "mouse", "keyboard", "cell phone"],
        "Другое": []
    }

    categorized = {cat: [] for cat in categories}
    uncategorized = []

    for cls in classes:
        found = False
        for cat, items in categories.items():
            if cls in items:
                categorized[cat].append(cls)
                found = True
                break
        if not found:
            uncategorized.append(cls)

    for cat, items in categorized.items():
        if items:
            result += f"\n**{cat}:** {', '.join(items)}\n"

    if uncategorized:
        result += f"\n**Остальные:** {', '.join(uncategorized[:20])}..."

    return result


# Создание интерфейса Gradio
def create_interface():
    """Создание веб-интерфейса"""

    with gr.Blocks(title="🗺️ Детектор объектов на картах с YOLO", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🗺️ Детектор объектов на картах с YOLO

        Загрузите изображение карты и обнаруживайте объекты с помощью нейросети YOLO.
        Поддерживается детекция 80+ классов объектов.
        """)

        with gr.Tab("⚙️ Настройка модели"):
            gr.Markdown("### Выберите и загрузите модель YOLO")

            model_choice = gr.Dropdown(
                choices=[
                    "YOLOv8 Nano (быстрая)",
                    "YOLOv8 Small",
                    "YOLOv8 Medium",
                    "YOLOv8 Large (точная)"
                ],
                value="YOLOv8 Nano (быстрая)",
                label="Модель YOLO"
            )

            load_btn = gr.Button("🚀 Загрузить модель", variant="primary")
            status_text = gr.Markdown("")

            load_btn.click(
                fn=initialize_detector,
                inputs=[model_choice],
                outputs=[status_text]
            )

            gr.Markdown("---")
            classes_btn = gr.Button("📋 Показать доступные классы")
            classes_output = gr.Markdown("")

            classes_btn.click(
                fn=get_available_classes,
                outputs=[classes_output]
            )

        with gr.Tab("🔍 Детекция всех объектов"):
            gr.Markdown("### Обнаружение всех объектов на карте")

            with gr.Row():
                with gr.Column():
                    input_image1 = gr.Image(type="numpy", label="Загрузите карту")
                    confidence1 = gr.Slider(0, 1, 0.25, step=0.05, label="Порог уверенности")
                    iou1 = gr.Slider(0, 1, 0.45, step=0.05, label="IoU порог")
                    detect_btn1 = gr.Button("🔍 Обнаружить объекты", variant="primary")

                with gr.Column():
                    output_image1 = gr.Image(label="Результат")
                    output_stats1 = gr.Markdown("")

            detect_btn1.click(
                fn=detect_all_objects,
                inputs=[input_image1, confidence1, iou1],
                outputs=[output_image1, output_stats1]
            )

            gr.Examples(
                examples=[],
                inputs=input_image1,
                label="Примеры изображений"
            )

        with gr.Tab("🎯 Поиск конкретного объекта"):
            gr.Markdown("### Поиск объектов определенного класса")

            with gr.Row():
                with gr.Column():
                    input_image2 = gr.Image(type="numpy", label="Загрузите карту")
                    target_class = gr.Textbox(
                        label="Класс для поиска",
                        placeholder="Например: car, person, bicycle",
                        value="car"
                    )
                    confidence2 = gr.Slider(0, 1, 0.25, step=0.05, label="Порог уверенности")
                    detect_btn2 = gr.Button("🎯 Найти объекты", variant="primary")

                with gr.Column():
                    output_image2 = gr.Image(label="Результат")
                    output_stats2 = gr.Markdown("")

            detect_btn2.click(
                fn=detect_specific,
                inputs=[input_image2, target_class, confidence2],
                outputs=[output_image2, output_stats2]
            )

        with gr.Tab("🔄 Замена объектов"):
            gr.Markdown("""
            ### Поиск и замена объектов на изображении

            **Примеры использования:**
            - Замените мяч на куб
            - Замените автомобили на сферы
            - Удалите нежелательные объекты
            - Наложите свое изображение
            """)

            with gr.Row():
                with gr.Column():
                    input_image3 = gr.Image(type="numpy", label="Загрузите изображение")

                    source_class_input = gr.Textbox(
                        label="Класс объектов для замены",
                        placeholder="Например: sports ball, car, person",
                        value="sports ball"
                    )

                    replacement_type_input = gr.Radio(
                        choices=["cube", "sphere", "blur", "remove", "custom"],
                        value="cube",
                        label="Тип замены",
                        info="cube=куб, sphere=сфера, blur=размытие, remove=удалить, custom=свое изображение"
                    )

                    custom_image_input = gr.Image(
                        type="numpy",
                        label="Свое изображение (только для custom)",
                        visible=True
                    )

                    confidence3 = gr.Slider(0, 1, 0.25, step=0.05, label="Порог уверенности")

                    use_inpaint = gr.Checkbox(
                        value=True,
                        label="Заполнять фон при замене",
                        info="Использовать инпейнтинг для удаления старого объекта"
                    )

                    replace_btn = gr.Button("🔄 Заменить объекты", variant="primary")

                with gr.Column():
                    output_image3 = gr.Image(label="Результат")
                    output_stats3 = gr.Markdown("")

                    gr.Markdown("""
                    **💡 Советы:**
                    - Для мячей используйте класс "sports ball"
                    - Для людей используйте "person"
                    - Включите "Заполнять фон" для лучшего результата
                    - Попробуйте разные типы замены!
                    """)

            replace_btn.click(
                fn=replace_objects_on_image,
                inputs=[input_image3, source_class_input, replacement_type_input,
                        custom_image_input, confidence3, use_inpaint],
                outputs=[output_image3, output_stats3]
            )

        with gr.Tab("ℹ️ Информация"):
            gr.Markdown("""
            ## Как использовать:

            1. **Настройка модели**: Выберите модель YOLO и нажмите "Загрузить модель"
               - Nano - самая быстрая, но менее точная
               - Large - самая точная, но медленнее

            2. **Детекция всех объектов**: Загрузите изображение карты и нажмите "Обнаружить"

            3. **Поиск конкретного объекта**: Укажите класс (например, "car", "person") и найдите все такие объекты

            4. **Замена объектов**: 
               - Загрузите изображение (например, человек держит мяч)
               - Укажите класс для замены (например, "sports ball" для мяча)
               - Выберите тип замены (cube, sphere, blur, remove, custom)
               - Нажмите "Заменить объекты"

            ## Примеры замены:

            - 🏀 **Мяч → Куб**: sports ball / cube
            - 🚗 **Машина → Сфера**: car / sphere
            - 👤 **Размытие лиц**: person / blur
            - ❌ **Удаление объектов**: любой класс / remove
            - 🖼️ **Свое изображение**: любой класс / custom + загрузите свое изображение

            ## Поддерживаемые классы:

            Модель распознает 80 классов объектов COCO dataset, включая:
            - 🚗 Транспорт: car, bus, truck, motorcycle, bicycle
            - 👤 Люди: person
            - 🐕 Животные: dog, cat, bird, horse
            - 🚦 Дорожные объекты: traffic light, stop sign
            - И многое другое!

            ## Параметры:

            - **Порог уверенности**: Минимальная уверенность модели (выше = меньше ложных детекций)
            - **IoU порог**: Порог для подавления перекрывающихся детекций

            ## Требования:
            ```bash
            pip install ultralytics gradio opencv-python pillow torch
            ```
            """)

    return demo


if __name__ == "__main__":
    print("🚀 Запуск интерфейса детектора объектов...")
    print("📦 Установите зависимости: pip install ultralytics gradio opencv-python pillow torch")
    print("\n⏳ Создание интерфейса...")

    demo = create_interface()

    print("\n✅ Интерфейс создан! Запуск сервера...")
    print("🌐 Откройте браузер и перейдите по адресу:")
    print("   http://127.0.0.1:7860")
    print("   или")
    print("   http://localhost:7860")
    print("\n⚠️ Для остановки нажмите Ctrl+C\n")

    demo.launch(
        share=False,
        server_name="127.0.0.1",  # Изменено на 127.0.0.1
        server_port=7860,
        inbrowser=True,  # Автоматически откроет браузер
        quiet=False  # Показывать логи
    )