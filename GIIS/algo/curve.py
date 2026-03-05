import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox,
                             QHBoxLayout, QGraphicsView, QGraphicsScene)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor


class CurveAlgorithmDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Curve Drawing Algorithm")
        self.setGeometry(130, 120, 300, 200)

        layout = QVBoxLayout()
        self.label = QLabel("Choose a curve algorithm:")
        layout.addWidget(self.label)

        self.hermite_button = QPushButton("Hermite Curve")
        self.hermite_button.setCheckable(True)
        self.hermite_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.hermite_button)

        self.bezier_button = QPushButton("Bezier Curve")
        self.bezier_button.setCheckable(True)
        self.bezier_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.bezier_button)

        self.bspline_button = QPushButton("B-Spline Curve")
        self.bspline_button.setCheckable(True)
        self.bspline_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.bspline_button)

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
            for button in (self.hermite_button, self.bezier_button, self.bspline_button):
                if button != sender:
                    button.setChecked(False)

    def get_selection(self):
        if self.hermite_button.isChecked():
            return "Hermite", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        elif self.bezier_button.isChecked():
            return "Bezier", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        elif self.bspline_button.isChecked():
            return "BSpline", self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()
        return None, self.debug_mode_checkbox.isChecked(), self.clear_canvas_checkbox.isChecked()


class CurveDrawClass(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.temp_pixels = None
        self.pixel_size = 10
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1200, 850)
        self.setScene(self.scene)

        self.control_points = []
        self.algorithm = None
        self.debug_mode = False
        self.clear_canvas_after_drawing = True

    def set_algorithm(self, algorithm, debug_mode=False, clear_canvas_after_drawing=True):
        self.algorithm = algorithm
        self.debug_mode = debug_mode
        self.clear_canvas_after_drawing = clear_canvas_after_drawing
        self.control_points = []
        self.temp_pixels =[]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            grid_x = int(pos.x() // self.pixel_size) * self.pixel_size
            grid_y = int(pos.y() // self.pixel_size) * self.pixel_size


            temp_pixel = self.scene.addRect(
                grid_x, grid_y, self.pixel_size, self.pixel_size,
                QColor(255, 0, 0), QColor(255, 0, 0)
            )

            self.temp_pixels.append(temp_pixel)
            self.control_points.append(QPointF(grid_x, grid_y))

            if (
                    self.algorithm == "Hermite" and len(self.control_points) == 4 or
                    self.algorithm == "Bezier" and len(self.control_points) == 4 or
                    self.algorithm == "BSpline" and len(self.control_points) >= 8
            ):
                for pixel in self.temp_pixels:
                    self.scene.removeItem(pixel)
                self.temp_pixels.clear()

                self.draw_curve()
                self.control_points = []



    def draw_curve(self):
        if self.algorithm == "Hermite" and len(self.control_points) == 4:
            p1, p4 = self.control_points[0], self.control_points[1]
            r1, r4 = self.control_points[2], self.control_points[3]
            if self.debug_mode:
                print(f"Drawing Hermite curve with P1={p1}, P4={p4}, R1={r1}, R4={r4}")
            if self.clear_canvas_after_drawing:
                self.scene.clear()
                self.draw_grid()
            self.draw_hermite(p1, p4, r1, r4, self.debug_mode)

        elif self.algorithm == "Bezier" and len(self.control_points) >= 4:
            if self.debug_mode:
                print(f"Drawing Bezier curve with control points: {self.control_points}")
            if self.clear_canvas_after_drawing:
                self.scene.clear()
                self.draw_grid()
            self.draw_bezier(self.control_points, self.debug_mode)

        elif self.algorithm == "BSpline" and len(self.control_points) >= 4:
            if self.debug_mode:
                print(f"Drawing B-spline curve with control points: {self.control_points}")
            if self.clear_canvas_after_drawing:
                self.scene.clear()
                self.draw_grid()
            self.draw_bspline(self.control_points, self.debug_mode)

    def draw_grid(self):
        self.scene.clear()
        rect = self.scene.sceneRect()
        for x in range(0, int(rect.width()), self.pixel_size):
            for y in range(0, int(rect.height()), self.pixel_size):
                self.scene.addRect(x, y, self.pixel_size, self.pixel_size, QColor(230, 230, 230))

    def draw_hermite(self, p1, p4, r1, r4, debug_mode):
        H = np.array([
            [2, -2, 1, 1],
            [-3, 3, -2, -1],
            [0, 0, 1, 0],
            [1, 0, 0, 0]
        ])
        Gx = np.array([p1.x(), p4.x(), r1.x() - p1.x(), r4.x() - p4.x()])
        Gy = np.array([p1.y(), p4.y(), r1.y() - p1.y(), r4.y() - p4.y()])

        t_values = np.linspace(0, 1, 1000)
        for t in t_values:
            T = np.array([t**3, t**2, t, 1])
            x = T @ H @ Gx
            y = T @ H @ Gy
            self.fill_pixel(int(x), int(y))
            if debug_mode:
                QApplication.processEvents()
                time.sleep(0.001)
                print(f"Hermite point: ({x}, {y})")

    def draw_bezier(self, control_points, debug_mode):
        n = len(control_points) - 1
        t_values = np.linspace(0, 1, 1000)
        for t in t_values:
            x, y = 0, 0
            for i, point in enumerate(control_points):
                bernstein = self.bernstein_polynomial(i, n, t)
                x += bernstein * point.x()
                y += bernstein * point.y()
            self.fill_pixel(int(x), int(y))
            if debug_mode:
                QApplication.processEvents()
                time.sleep(0.001)
                print(f"Bezier point: ({x}, {y})")

    def bernstein_polynomial(self, i, n, t):
        from math import comb
        return comb(n, i) * (t**i) * ((1 - t)**(n - i))

    def draw_bspline(self, control_points, debug_mode):
        B = np.array([
            [-1 / 6, 3 / 6, -3 / 6, 1 / 6],
            [3 / 6, -6 / 6, 3 / 6, 0],
            [-3 / 6, 0, 3 / 6, 0],
            [1 / 6, 4 / 6, 1 / 6, 0]
        ])

        for i in range(len(control_points) - 3):
            Gx = np.array([control_points[i].x(), control_points[i + 1].x(),
                           control_points[i + 2].x(), control_points[i + 3].x()])
            Gy = np.array([control_points[i].y(), control_points[i + 1].y(),
                           control_points[i + 2].y(), control_points[i + 3].y()])

            t_values = np.linspace(0, 1, 100)
            for t in t_values:
                T = np.array([t**3, t**2, t, 1])
                x = T @ B @ Gx
                y = T @ B @ Gy
                self.fill_pixel(int(x), int(y))
                if debug_mode:
                    QApplication.processEvents()
                    time.sleep(0.001)
                    print(f"B-spline point: ({x}, {y})")

    def fill_pixel(self, x, y):
        self.scene.addRect(
            x // self.pixel_size * self.pixel_size,
            y // self.pixel_size * self.pixel_size,
            self.pixel_size,
            self.pixel_size,
            QColor(0, 0, 0),
            QColor(0, 0, 0),
        )