import time
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox,
                             QHBoxLayout, QGraphicsView, QGraphicsScene)


class CircleAlgorithmDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Second-Order Curve")
        self.setGeometry(130, 120, 300, 200)

        layout = QVBoxLayout()
        self.label = QLabel("Choose a curve:")
        layout.addWidget(self.label)

        self.circle_button = QPushButton("Circle")
        self.circle_button.setCheckable(True)
        self.circle_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.circle_button)

        self.ellipse_button = QPushButton("Ellipse")
        self.ellipse_button.setCheckable(True)
        self.ellipse_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.ellipse_button)

        self.hyperbola_button = QPushButton("Hyperbola")
        self.hyperbola_button.setCheckable(True)
        self.hyperbola_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.hyperbola_button)

        self.parabola_button = QPushButton("Parabola")
        self.parabola_button.setCheckable(True)
        self.parabola_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.parabola_button)

        mode_layout = QHBoxLayout()

        self.debug_mode_checkbox = QCheckBox("Debug Mode")
        mode_layout.addWidget(self.debug_mode_checkbox)

        self.clear_canvas_checkbox = QCheckBox("Clear Canvas After Drawing")
        self.clear_canvas_checkbox.setChecked(True)
        mode_layout.addWidget(self.clear_canvas_checkbox)

        layout.addLayout(mode_layout)
        layout.addStretch()

        self.draw_button = QPushButton("Draw Curve")
        self.draw_button.clicked.connect(self.accept)
        layout.addWidget(self.draw_button)

        self.setLayout(layout)

    def on_button_click(self):
        sender = self.sender()
        if sender.isChecked():
            for button in (self.circle_button, self.ellipse_button, self.hyperbola_button, self.parabola_button):
                if button != sender:
                    button.setChecked(False)

    def get_selection(self):
        if self.circle_button.isChecked():
            return "Circle", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        elif self.ellipse_button.isChecked():
            return "Ellipse", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        elif self.hyperbola_button.isChecked():
            return "Hyperbola", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        elif self.parabola_button.isChecked():
            return "Parabola", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        return None, self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()


class CircleDrawingArea(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.pixel_size = 10
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1200, 850)
        self.setScene(self.scene)

        self.start_points = []
        self.algorithm = None
        self.debug_mode = False
        self.clear_canvas_after_drawing = True

    def set_algorithm(self, algorithm, debug_mode, clear_canvas_after_drawing):
        self.algorithm = algorithm
        self.debug_mode = debug_mode
        self.clear_canvas_after_drawing = clear_canvas_after_drawing
        self.start_points = []

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            grid_x = int(pos.x() // self.pixel_size) * self.pixel_size
            grid_y = int(pos.y() // self.pixel_size) * self.pixel_size

            temp_pixel = self.scene.addRect(
                grid_x, grid_y, self.pixel_size, self.pixel_size,
                QColor(255, 0, 0), QColor(255, 0, 0)
            )

            self.start_points.append(QPoint(grid_x, grid_y))

            if (
                    (self.algorithm == "Ellipse" and len(self.start_points) == 3) or
                    (self.algorithm in ["Circle", "Hyperbola", "Parabola"] and len(self.start_points) == 2)
            ):
                self.scene.removeItem(temp_pixel)
                self.draw_shape()
                self.start_points = []

    def draw_shape(self):
        if self.algorithm == "Ellipse" and len(self.start_points) == 3:
            center = self.start_points[0]
            x_radius = abs(self.start_points[1].x() - center.x()) // self.pixel_size
            y_radius = abs(self.start_points[2].y() - center.y()) // self.pixel_size
            if self.debug_mode:
                print(f"Drawing Ellipse at {center} with radii ({x_radius}, {y_radius})")
            if self.clear_canvas_after_drawing:
                time.sleep(0.05)
                self.scene.clear()
                self.draw_grid()
            self.draw_ellipse(center, x_radius, y_radius, self.debug_mode)

        elif self.algorithm == "Circle" and len(self.start_points) == 2:
            dx = self.start_points[1].x() - self.start_points[0].x()
            dy = self.start_points[1].y() - self.start_points[0].y()
            radius = int(((dx ** 2 + dy ** 2) ** 0.5) // self.pixel_size)
            if self.debug_mode:
                print(f"Drawing Circle at {self.start_points[0]} with radius {radius}")
            if self.clear_canvas_after_drawing:
                time.sleep(0.05)
                self.scene.clear()
                self.draw_grid()
            self.draw_circle(self.start_points[0], radius, self.debug_mode)

        elif self.algorithm == "Hyperbola" and len(self.start_points) == 2:
            center = self.start_points[0]
            a = abs(self.start_points[1].x() - center.x()) // self.pixel_size
            if self.debug_mode:
                print(f"Drawing Hyperbola at {center} with a = {a}")
            if self.clear_canvas_after_drawing:
                time.sleep(0.05)
                self.scene.clear()
                self.draw_grid()
            self.draw_hyperbola(center, a, self.debug_mode)

        elif self.algorithm == "Parabola" and len(self.start_points) == 2:
            center = self.start_points[0]
            p = abs(self.start_points[1].y() - center.y()) // self.pixel_size
            if self.debug_mode:
                print(f"Drawing Parabola at {center} with p = {p}")
            if self.clear_canvas_after_drawing:
                time.sleep(0.05)
                self.scene.clear()
                self.draw_grid()
            self.draw_parabola(center, p, self.debug_mode)

    def draw_grid(self):
        self.scene.clear()
        rect = self.scene.sceneRect()
        for x in range(0, int(rect.width()), self.pixel_size):
            for y in range(0, int(rect.height()), self.pixel_size):
                self.scene.addRect(x, y, self.pixel_size, self.pixel_size, QColor(230, 230, 230))

    def draw_circle(self, center, radius, debug_mode):
        x0, y0 = center.x() // self.pixel_size, center.y() // self.pixel_size
        x, y = 0, radius
        d = 3 - 2 * radius

        while x <= y:
            self.fill_symmetric_points(x0, y0, x, y)
            if debug_mode:
                print(f"Circle: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def draw_ellipse(self, center, a, b, debug_mode):
        x0, y0 = center.x() // self.pixel_size, center.y() // self.pixel_size
        x, y = 0, b
        a2, b2 = a ** 2, b ** 2
        d = b2 - (a2 * b) + (0.25 * a2)

        while (b2 * x) < (a2 * y):
            self.fill_symmetric_points(x0, y0, x, y, ellipse_mode=True)
            if debug_mode:
                print(f"Ellipse Region 1: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)
            if d < 0:
                d += b2 * (2 * x + 3)
            else:
                d += b2 * (2 * x + 3) + a2 * (-2 * y + 2)
                y -= 1
            x += 1

        d = b2 * (x + 0.5) ** 2 + a2 * (y - 1) ** 2 - a2 * b2
        while y >= 0:
            self.fill_symmetric_points(x0, y0, x, y, ellipse_mode=True)
            if debug_mode:
                print(f"Ellipse Region 2: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)
            if d > 0:
                d += a2 * (-2 * y + 3)
            else:
                d += b2 * (2 * x + 2) + a2 * (-2 * y + 3)
                x += 1
            y -= 1

    def draw_hyperbola(self, center, a, debug_mode):
        x0, y0 = center.x() // self.pixel_size, center.y() // self.pixel_size
        x, y = a, 0
        a2, b2 = a ** 2, a ** 2

        d1 = b2 - a2 * (1 - 0.25)

        while b2 * x > a2 * y:
            self.fill_symmetric_points(x0, y0, x, y, symmetric=False)
            if debug_mode:
                print(f"Hyperbola Region 1: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)
            if d1 < 0:
                d1 += b2 * (2 * y + 3)
            else:
                d1 += b2 * (2 * y + 3) - a2 * (2 * x - 2)
                x += 1
            y += 1
            if x > 100 or y > 100:
                break

        d2 = b2 * (x + 0.5) ** 2 - a2 * (y + 1) ** 2 - a2 * b2
        
        while x < 100:
            self.fill_symmetric_points(x0, y0, x, y, symmetric=False)
            if debug_mode:
                print(f"Hyperbola Region 2: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)
            if d2 > 0:
                d2 -= a2 * (2 * x - 3)
            else:
                d2 += b2 * (2 * y + 2) - a2 * (2 * x - 3)
                y += 1
            x += 1

            if x > 100 or y > 100:
                break

    def draw_parabola(self, center, p, debug_mode):
        x0, y0 = center.x() // self.pixel_size, center.y() // self.pixel_size

        x, y = 0, 0
        d = 1 - 2 * p

        while x ** 2 < 4 * p * y:
            self.fill_symmetric_points(x0, y0, x, y, parabola_mode=True, upward=True)
            if debug_mode:
                print(f"Parabola Region 1: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)

            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * x + 3 - 4 * p
                y += 1
            x += 1

        d = (x + 0.5) ** 2 - 4 * p * (y + 1)
        while y < 100:
            self.fill_symmetric_points(x0, y0, x, y, parabola_mode=True, upward=True)
            if debug_mode:
                print(f"Parabola Region 2: ({x}, {y})")
                QApplication.processEvents()
                time.sleep(0.05)

            if d > 0:
                d += -4 * p + 2
            else:
                d += 2 * x - 4 * p + 2
                x += 1
            y += 1

    def fill_symmetric_points(self, x0, y0, x, y, symmetric=True, ellipse_mode=False, parabola_mode=False,
                              upward=False):
        if parabola_mode and upward:

            points = [
                (x0 + x, y0 - y),
                (x0 - x, y0 - y),
            ]
        elif parabola_mode:

            points = [
                (x0 + x, y0 + y),
                (x0 - x, y0 + y),
            ]
        elif ellipse_mode:

            points = [
                (x0 + x, y0 + y),
                (x0 - x, y0 + y),
                (x0 + x, y0 - y),
                (x0 - x, y0 - y),
            ]
        elif symmetric:
            points = [
                (x0 + x, y0 + y),
                (x0 - x, y0 + y),
                (x0 + x, y0 - y),
                (x0 - x, y0 - y),
                (x0 + y, y0 + x),
                (x0 - y, y0 + x),
                (x0 + y, y0 - x),
                (x0 - y, y0 - x),
            ]
        else:

            points = [
                (x0 + x, y0 + y),
                (x0 - x, y0 + y),
                (x0 + x, y0 - y),
                (x0 - x, y0 - y),
            ]
        for px, py in points:
            self.fill_pixel(px, py)

    def fill_pixel(self, x, y):
        self.scene.addRect(
            x * self.pixel_size,
            y * self.pixel_size,
            self.pixel_size,
            self.pixel_size,
            QColor(0, 0, 0),
            QColor(0, 0, 0),
        )
