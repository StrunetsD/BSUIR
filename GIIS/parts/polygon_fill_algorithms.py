import sys
import time

from PyQt5.QtWidgets import (
    QApplication, QInputDialog, QMessageBox, QPushButton,
)
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt, QPointF

try:
    from parts.polygon_algorithms import PolygonDrawer, ViewerWithPolygonMenu
except ModuleNotFoundError:
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from parts.polygon_algorithms import PolygonDrawer, ViewerWithPolygonMenu


class PolygonFillDrawer(PolygonDrawer):
    def __init__(self, pixel_size=3):
        super().__init__(pixel_size)

    def get_pixel_color(self, x, y):
        item = self.scene.itemAt(x * self.pixel_size, y * self.pixel_size, self.transform())
        if item:
            return item.brush().color()
        return QColor(255, 255, 255)

    def fill_pixel_color(self, x, y, color=QColor(0, 0, 0)):
        self.scene.addRect(
            x * self.pixel_size, y * self.pixel_size,
            self.pixel_size, self.pixel_size,
            QPen(QColor(0, 0, 0), 0), color
        )

    def seed_fill(self, x, y):
        if self.fill_algorithm == "Simple Seed Fill":
            self.simple_seed_fill(x, y)
        elif self.fill_algorithm == "Scanline Seed Fill":
            self.scanline_seed_fill(x, y)
        elif self.fill_algorithm == "Ordered Edge List":
            self.ordered_edge_list_fill()
        elif self.fill_algorithm == "Active Edge List":
            self.active_edge_list_fill()

    def simple_seed_fill(self, x, y):
        target_color = self.get_pixel_color(x, y)
        fill_color = QColor(0, 255, 0)

        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if self.get_pixel_color(cx, cy) == target_color:
                self.fill_pixel_color(cx, cy, fill_color)
                if self.debug_mode:
                    QApplication.processEvents()
                    time.sleep(self.fill_delay / 1000)
                stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])

    def scanline_seed_fill(self, x, y):
        target_color = self.get_pixel_color(x, y)
        fill_color = QColor(0, 255, 0)

        if target_color == fill_color:
            return

        stack = [(x, y)]
        visited = set()
        fill_pixels = []

        while stack:
            cx, cy = stack.pop()

            if (cx, cy) in visited:
                continue

            visited.add((cx, cy))

            left = cx
            while left >= 0 and self.get_pixel_color(left, cy) == target_color:
                left -= 1
            left += 1

            right = cx
            while right < self.scene.width() // self.pixel_size and self.get_pixel_color(right, cy) == target_color:
                right += 1
            right -= 1

            for px in range(left - 1, right + 1):
                fill_pixels.append((px, cy))
                visited.add((px, cy))

            for dy in [-1, 1]:
                for px in range(left, right + 1):
                    if (px, cy + dy) not in visited and self.get_pixel_color(px, cy + dy) == target_color:
                        stack.append((px, cy + dy))

        for px, py in fill_pixels:
            self.fill_pixel_color(px, py, fill_color)
            if self.debug_mode:
                QApplication.processEvents()
                time.sleep(self.fill_delay / 1000)

    def active_edge_list_fill(self):
        if len(self.polygon_points) < 3:
            return

        edges = []
        fill_color = QColor(0, 255, 0)

        n = len(self.polygon_points)
        for i in range(n):
            p1 = self.polygon_points[i]
            p2 = self.polygon_points[(i + 1) % n]

            if p1.y() == p2.y():
                continue

            if p1.y() > p2.y():
                p1, p2 = p2, p1

            dy = p2.y() - p1.y()
            dx = p2.x() - p1.x()
            inv_slope = dx / dy if dy != 0 else 0

            edges.append({
                "y_min": p1.y(),
                "y_max": p2.y(),
                "x": p1.x(),
                "inv_slope": inv_slope
            })

        edges.sort(key=lambda e: e["y_min"])

        y = min(edge["y_min"] for edge in edges)
        y_max = max(edge["y_max"] for edge in edges)
        active_edges = []

        while y <= y_max:
            active_edges.extend(edge for edge in edges if edge["y_min"] == y)
            active_edges = [edge for edge in active_edges if edge["y_max"] > y]
            active_edges.sort(key=lambda e: e["x"])

            for i in range(0, len(active_edges), 2):
                if i + 1 >= len(active_edges):
                    break

                x_start = int(active_edges[i]["x"] / self.pixel_size)
                x_end = int(active_edges[i + 1]["x"] / self.pixel_size)

                if x_start > x_end:
                    x_start, x_end = x_end, x_start

                x_start += 1
                x_end -= 1

                if x_start <= x_end:
                    for x in range(x_start, x_end + 1):
                        self.fill_pixel_color(x, int(y / self.pixel_size), fill_color)
                        if self.debug_mode:
                            QApplication.processEvents()
                            time.sleep(self.fill_delay / 1000)

            for edge in active_edges:
                edge["x"] += edge["inv_slope"] * self.pixel_size

            y += self.pixel_size

    def ordered_edge_list_fill(self):
        if len(self.polygon_points) < 3:
            return

        edges = []
        fill_color = QColor(0, 255, 0)

        n = len(self.polygon_points)
        for i in range(n):
            p1 = self.polygon_points[i]
            p2 = self.polygon_points[(i + 1) % n]

            if p1.y() == p2.y():
                continue

            if p1.y() > p2.y():
                p1, p2 = p2, p1

            y_min = p1.y() / self.pixel_size
            y_max = p2.y() / self.pixel_size
            x = p1.x() / self.pixel_size
            dx = (p2.x() - p1.x()) / (p2.y() - p1.y()) / self.pixel_size * self.pixel_size

            edges.append({
                "y_min": y_min,
                "y_max": y_max,
                "x": x,
                "dx": dx
            })

        edges.sort(key=lambda e: e["y_min"])

        y = int(min(edge["y_min"] for edge in edges))
        y_max = int(max(edge["y_max"] for edge in edges)) + 1
        active_edges = []

        while y <= y_max:
            for edge in edges:
                if int(edge["y_min"]) == y:
                    active_edges.append(edge)

            active_edges = [e for e in active_edges if int(e["y_max"]) > y]
            active_edges.sort(key=lambda e: e["x"])

            for i in range(0, len(active_edges), 2):
                if i + 1 >= len(active_edges):
                    break

                x_start = int(active_edges[i]["x"])
                x_end = int(active_edges[i + 1]["x"])

                if x_start > x_end:
                    x_start, x_end = x_end, x_start

                for x in range(x_start, x_end + 1):
                    self.fill_pixel_color(x, y, fill_color)
                    if self.debug_mode:
                        QApplication.processEvents()
                        time.sleep(self.fill_delay / 1000)

            for edge in active_edges:
                edge["x"] += edge["dx"]

            y += 1


class ViewerWithPolygonFillMenu(ViewerWithPolygonMenu):
    def _create_drawer(self, pixel_size):
        return PolygonFillDrawer(pixel_size)

    def __init__(self, pixel_size=10):
        super().__init__(pixel_size)
        self.setWindowTitle("Polygon Fill")

        self.seed_fill_button = QPushButton("Seed Fill")
        self.seed_fill_button.clicked.connect(self.start_seed_fill)
        self.button_layout.insertWidget(
            self.button_layout.count() - 1,
            self.seed_fill_button
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ViewerWithPolygonFillMenu(pixel_size=10)
    viewer.show()
    sys.exit(app.exec_())