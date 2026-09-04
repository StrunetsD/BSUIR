import time
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox,
                             QHBoxLayout, QGraphicsView, QGraphicsScene, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QPen, QIntValidator


class LineDrawingMixin:
    def bresenham(self, start, end, debug_mode=False):
        x1 = int(start.x() // self.pixel_size)
        y1 = int(start.y() // self.pixel_size)
        x2 = int(end.x() // self.pixel_size)
        y2 = int(end.y() // self.pixel_size)
        dx = x2 - x1
        dy = y2 - y1
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        dx = abs(dx)
        dy = abs(dy)
        err = dx - dy
        while True:
            self.fill_pixel(x1, y1)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def cda(self, start, end, debug_mode=False):
        x1 = start.x() / self.pixel_size
        y1 = start.y() / self.pixel_size
        x2 = end.x() / self.pixel_size
        y2 = end.y() / self.pixel_size
        dx = x2 - x1
        dy = y2 - y1
        steps = int(max(abs(dx), abs(dy)))
        if steps == 0:
            self.fill_pixel(int(x1), int(y1))
            return
        x_inc = dx / steps
        y_inc = dy / steps
        x, y = x1, y1
        for _ in range(steps + 1):
            self.fill_pixel(int(x), int(y))
            x += x_inc
            y += y_inc

    def wu(self, start, end, debug_mode=False):
        x1 = start.x() / self.pixel_size
        y1 = start.y() / self.pixel_size
        x2 = end.x() / self.pixel_size
        y2 = end.y() / self.pixel_size

        def ipart(v): return int(v)
        def round_(v): return ipart(v + 0.5)
        def fpart(v): return v - ipart(v)
        def rfpart(v): return 1 - fpart(v)

        def plot(x, y, c):
            c = 1 - c
            color = QColor(int(255 * c), int(255 * c), int(255 * c))
            self.scene.addRect(x * self.pixel_size, y * self.pixel_size,
                               self.pixel_size, self.pixel_size, QPen(color), color)

        steep = abs(y2 - y1) > abs(x2 - x1)
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        dx = x2 - x1
        dy = y2 - y1
        gradient = dy / dx if dx != 0 else 1

        xend = round_(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = rfpart(x1 + 0.5)
        xpxl1 = ipart(xend)
        ypxl1 = ipart(yend)
        if steep:
            plot(ypxl1, xpxl1, rfpart(yend) * xgap)
            plot(ypxl1 + 1, xpxl1, fpart(yend) * xgap)
        else:
            plot(xpxl1, ypxl1, rfpart(yend) * xgap)
            plot(xpxl1, ypxl1 + 1, fpart(yend) * xgap)
        intery = yend + gradient

        xend = round_(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = fpart(x2 + 0.5)
        xpxl2 = ipart(xend)
        ypxl2 = ipart(yend)
        if steep:
            plot(ypxl2, xpxl2, rfpart(yend) * xgap)
            plot(ypxl2 + 1, xpxl2, fpart(yend) * xgap)
        else:
            plot(xpxl2, ypxl2, rfpart(yend) * xgap)
            plot(xpxl2, ypxl2 + 1, fpart(yend) * xgap)

        for x in range(xpxl1 + 1, xpxl2):
            if steep:
                plot(ipart(intery), x, rfpart(intery))
                plot(ipart(intery) + 1, x, fpart(intery))
            else:
                plot(x, ipart(intery), rfpart(intery))
                plot(x, ipart(intery) + 1, fpart(intery))
            intery += gradient


class LineAlgorithmDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Drawing Algorithm")
        self.setGeometry(130, 120, 400, 400)

        layout = QVBoxLayout()
        self.label = QLabel("Choose an algorithm:")
        layout.addWidget(self.label)

        self.cda_button = QPushButton("CDA")
        self.cda_button.setCheckable(True)
        self.cda_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.cda_button)

        self.bresenham_button = QPushButton("Bresenham")
        self.bresenham_button.setCheckable(True)
        self.bresenham_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.bresenham_button)

        self.wu_button = QPushButton("Wu's Algorithm")
        self.wu_button.setCheckable(True)
        self.wu_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.wu_button)

        coords_group = QGroupBox("Coordinates")
        coords_layout = QVBoxLayout()

        self.use_coords_checkbox = QCheckBox("Use custom coordinates")
        self.use_coords_checkbox.toggled.connect(self.toggle_inputs)
        coords_layout.addWidget(self.use_coords_checkbox)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start point:"))
        start_layout.addWidget(QLabel("X:"))
        self.x1_input = QLineEdit()
        self.x1_input.setValidator(QIntValidator(0, 120))
        self.x1_input.setPlaceholderText("0")
        start_layout.addWidget(self.x1_input)
        start_layout.addWidget(QLabel("Y:"))
        self.y1_input = QLineEdit()
        self.y1_input.setValidator(QIntValidator(0, 85))
        self.y1_input.setPlaceholderText("0")
        start_layout.addWidget(self.y1_input)
        coords_layout.addLayout(start_layout)

        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End point:"))
        end_layout.addWidget(QLabel("X:"))
        self.x2_input = QLineEdit()
        self.x2_input.setValidator(QIntValidator(0, 120))
        self.x2_input.setPlaceholderText("10")
        end_layout.addWidget(self.x2_input)
        end_layout.addWidget(QLabel("Y:"))
        self.y2_input = QLineEdit()
        self.y2_input.setValidator(QIntValidator(0, 85))
        self.y2_input.setPlaceholderText("10")
        end_layout.addWidget(self.y2_input)
        coords_layout.addLayout(end_layout)

        coords_group.setLayout(coords_layout)
        layout.addWidget(coords_group)

        self.toggle_inputs(False)

        mode_layout = QHBoxLayout()

        self.debug_mode_checkbox = QCheckBox("Debug Mode")
        mode_layout.addWidget(self.debug_mode_checkbox)

        self.clear_canvas_checkbox = QCheckBox("Clear Canvas After Drawing")
        self.clear_canvas_checkbox.setChecked(True)
        mode_layout.addWidget(self.clear_canvas_checkbox)

        layout.addLayout(mode_layout)
        layout.addStretch()

        self.draw_button = QPushButton("Draw Line")
        self.draw_button.clicked.connect(self.accept)
        layout.addWidget(self.draw_button)

        self.setLayout(layout)

    def on_button_click(self):
        sender = self.sender()
        if sender.isChecked():
            for button in (self.bresenham_button, self.cda_button, self.wu_button):
                if button != sender:
                    button.setChecked(False)

    def toggle_inputs(self, checked):
        self.x1_input.setEnabled(checked)
        self.y1_input.setEnabled(checked)
        self.x2_input.setEnabled(checked)
        self.y2_input.setEnabled(checked)

    def get_selection(self):
        algorithm = None
        if self.cda_button.isChecked():
            algorithm = "CDA"
        elif self.bresenham_button.isChecked():
            algorithm = "Bresenham"
        elif self.wu_button.isChecked():
            algorithm = "Wu's Algorithm"

        coordinates = None
        if self.use_coords_checkbox.isChecked():
            x1 = int(self.x1_input.text()) if self.x1_input.text() else 0
            y1 = int(self.y1_input.text()) if self.y1_input.text() else 0
            x2 = int(self.x2_input.text()) if self.x2_input.text() else 10
            y2 = int(self.y2_input.text()) if self.y2_input.text() else 10
            coordinates = (x1, y1, x2, y2)

        return (algorithm,
                self.debug_mode_checkbox.isChecked(),
                self.clear_canvas_checkbox.isChecked(),
                coordinates)


class LineDrawingArea(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.pixel_size = 10
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1200, 850)
        self.setScene(self.scene)

        self.start_point = None
        self.end_point = None
        self.algorithm = None
        self.debug_mode = False
        self.clear_canvas_after_drawing = True

    def set_algorithm(self, algorithm, debug_mode, clear_canvas_after_drawing, coordinates=None):
        self.algorithm = algorithm
        self.debug_mode = debug_mode
        self.clear_canvas_after_drawing = clear_canvas_after_drawing
        self.start_point = None

        if coordinates is not None:
            x1, y1, x2, y2 = coordinates
            self.start_point = QPoint(x1 * self.pixel_size, y1 * self.pixel_size)
            self.end_point = QPoint(x2 * self.pixel_size, y2 * self.pixel_size)
            self.draw_line()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            grid_x = int(pos.x() // self.pixel_size) * self.pixel_size
            grid_y = int(pos.y() // self.pixel_size) * self.pixel_size

            if self.start_point is None:
                self.start_point = QPoint(grid_x, grid_y)
            else:
                self.end_point = QPoint(grid_x, grid_y)
                self.draw_line()
                self.start_point = None

    def draw_line(self):
        if self.start_point is not None and self.end_point is not None and self.algorithm:
            if self.debug_mode:
                print(f"Drawing line from {self.start_point} to {self.end_point} using {self.algorithm}")
            if self.clear_canvas_after_drawing:
                self.scene.clear()
                self.draw_grid()
            self.drawLine(self.start_point, self.end_point)

    def draw_grid(self):
        self.scene.clear()
        rect = self.scene.sceneRect()
        for x in range(0, int(rect.width()), self.pixel_size):
            for y in range(0, int(rect.height()), self.pixel_size):
                self.scene.addRect(x, y, self.pixel_size, self.pixel_size, QColor(230, 230, 230))

    def drawLine(self, start, end):
        if self.algorithm == "CDA":
            self.cda(start, end, self.debug_mode)
        elif self.algorithm == "Bresenham":
            self.bresenham(start, end, self.debug_mode)
        elif self.algorithm == "Wu's Algorithm":
            self.wu(start, end, self.debug_mode)

    def cda(self, start, end, debug_mode):
        x1, y1 = start.x() // self.pixel_size, start.y() // self.pixel_size
        x2, y2 = end.x() // self.pixel_size, end.y() // self.pixel_size
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))

        if steps == 0:
            self.fill_pixel(int(x1), int(y1))
            return

        x_inc = dx / float(steps)
        y_inc = dy / float(steps)

        x, y = x1, y1
        for _ in range(steps + 1):
            self.fill_pixel(int(x), int(y))
            if debug_mode:
                print(f"CDA: ({int(x)}, {int(y)})")
                QApplication.processEvents()
                time.sleep(0.05)
            x += x_inc
            y += y_inc

    def bresenham(self, start, end, debug_mode):
        x1, y1 = start.x() // self.pixel_size, start.y() // self.pixel_size
        x2, y2 = end.x() // self.pixel_size, end.y() // self.pixel_size
        dx = x2 - x1
        dy = y2 - y1
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        dx = abs(dx)
        dy = abs(dy)
        err = 2*dy-dx
        i=1

        while i<=dx+1:
            self.fill_pixel(x1, y1)
            if debug_mode:
                print(f"Bresenham: ({x1}, {y1})")
                QApplication.processEvents()
                time.sleep(0.05)
            if err>=0:
                y1 += sy
                err-=2*dx
            x1 += sx
            err+=2*dy
            i+=1

    def wu(self, start, end, debug_mode):
        x1, y1 = start.x() / self.pixel_size, start.y() / self.pixel_size
        x2, y2 = end.x() / self.pixel_size, end.y() / self.pixel_size

        def ipart(x):
            return int(x)

        def round_(x):
            return ipart(x + 0.5)

        def fpart(x):
            return x - ipart(x)

        def rfpart(x):
            return 1 - fpart(x)

        def plot(x, y, c):
            c = 1 - c
            color = QColor(int(255 * c), int(255 * c), int(255 * c))
            self.scene.addRect(x * self.pixel_size, y * self.pixel_size,
                               self.pixel_size, self.pixel_size, color, color)

        steep = abs(y2 - y1) > abs(x2 - x1)
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2

        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        dx = x2 - x1
        dy = y2 - y1
        gradient = dy / dx if dx != 0 else 1

        xend = round_(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = rfpart(x1 + 0.5)
        xpxl1 = ipart(xend)
        ypxl1 = ipart(yend)
        if steep:
            plot(ypxl1, xpxl1, rfpart(yend) * xgap)
            plot(ypxl1 + 1, xpxl1, fpart(yend) * xgap)
        else:
            plot(xpxl1, ypxl1, rfpart(yend) * xgap)
            plot(xpxl1, ypxl1 + 1, fpart(yend) * xgap)
        intery = yend + gradient

        xend = round_(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = fpart(x2 + 0.5)
        xpxl2 = ipart(xend)
        ypxl2 = ipart(yend)
        if steep:
            plot(ypxl2, xpxl2, rfpart(yend) * xgap)
            plot(ypxl2 + 1, xpxl2, fpart(yend) * xgap)
        else:
            plot(xpxl2, ypxl2, rfpart(yend) * xgap)
            plot(xpxl2, ypxl2 + 1, fpart(yend) * xgap)

        for x in range(xpxl1 + 1, xpxl2):
            if steep:
                plot(ipart(intery), x, rfpart(intery))
                plot(ipart(intery) + 1, x, fpart(intery))
            else:
                plot(x, ipart(intery), rfpart(intery))
                plot(x, ipart(intery) + 1, fpart(intery))
            if debug_mode:
                print(f"Wu: ({x}, {intery})")
                QApplication.processEvents()
                time.sleep(0.05)
            intery += gradient

    def fill_pixel(self, x, y):
        self.scene.addRect(
            x * self.pixel_size,
            y * self.pixel_size,
            self.pixel_size,
            self.pixel_size,
            QColor(0, 0, 0),
            QColor(0, 0, 0),
        )