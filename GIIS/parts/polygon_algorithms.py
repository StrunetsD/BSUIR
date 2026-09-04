import math
import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QDialog, QVBoxLayout,
    QHBoxLayout, QPushButton, QComboBox, QMessageBox, QInputDialog, QCheckBox,
)
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt, QPointF

try:
    from parts.line_algorithm import LineDrawingMixin
except ModuleNotFoundError:
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from parts.line_algorithm import LineDrawingMixin

# Length of the normal arrow in scene pixels
NORMAL_LENGTH = 40
# Half-angle of the arrowhead in degrees
ARROW_ANGLE = 25
# Arrowhead arm length in scene pixels
ARROW_SIZE = 10


class PolygonDrawer(LineDrawingMixin, QGraphicsView):
    def __init__(self, pixel_size=3):
        QGraphicsView.__init__(self)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1000, 800)
        self.setScene(self.scene)

        self.pixel_size = pixel_size
        self.polygon_points = []
        self.is_drawing = True
        self.line_algorithm = "Bresenham"
        self.debug_mode = False

        self.line_start_point = None
        self.line_end_point = None
        self.is_marking_line = False
        self.is_selecting_seed = False
        self.seed_point = None

        self.fill_algorithm = "Simple Seed Fill"
        self.fill_delay = 10

        # Storage for normal graphic items so they can be removed later
        self._normal_items = []

        self.draw_grid()

    # ------------------------------------------------------------------
    # Pixel helpers
    # ------------------------------------------------------------------

    def fill_pixel(self, x, y):
        self.scene.addRect(
            x * self.pixel_size, y * self.pixel_size,
            self.pixel_size, self.pixel_size,
            QPen(Qt.black), QColor(0, 0, 0)
        )

    def fill_pixel_red(self, x, y):
        dot_size = self.pixel_size * 2
        self.scene.addRect(
            (x * self.pixel_size - dot_size // 2) + 5,
            (y * self.pixel_size - dot_size // 2) + 5,
            dot_size, dot_size,
            QPen(Qt.black), QColor(255, 0, 0)
        )

    def draw_grid(self):
        pass

    # ------------------------------------------------------------------
    # Line drawing
    # ------------------------------------------------------------------

    def set_line_algorithm(self, algorithm):
        self.line_algorithm = algorithm

    def draw_line(self, start, end):
        if self.line_algorithm == "Bresenham":
            self.bresenham(start, end, self.debug_mode)
        elif self.line_algorithm == "CDA":
            self.cda(start, end, self.debug_mode)
        elif self.line_algorithm == "Wu":
            self.wu(start, end, self.debug_mode)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def start_drawing(self):
        self.is_drawing = True
        self.polygon_points = []

    def reset(self):
        self.scene.clear()
        self.polygon_points = []
        self.is_drawing = True
        self._normal_items = []
        self.draw_grid()

    def toggle_debug_mode(self, state):
        self.debug_mode = state == Qt.Checked

    def start_seed_selection(self):
        self.is_selecting_seed = True
        self.seed_point = None

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        scene_position = self.mapToScene(event.pos())
        grid_x = int(scene_position.x() // self.pixel_size)
        grid_y = int(scene_position.y() // self.pixel_size)

        if self.is_selecting_seed:
            self.seed_point = QPointF(grid_x, grid_y)
            self.is_selecting_seed = False
            self.seed_fill(grid_x, grid_y)
        elif self.is_drawing:
            self.polygon_points.append(QPointF(grid_x * self.pixel_size, grid_y * self.pixel_size))
            self.scene.addRect(
                grid_x * self.pixel_size, grid_y * self.pixel_size,
                self.pixel_size, self.pixel_size,
                QPen(Qt.black), QColor(0, 0, 0)
            )
            if len(self.polygon_points) > 1:
                prev_point = self.polygon_points[-2]
                current_point = self.polygon_points[-1]
                self.draw_line(prev_point, current_point)
        elif self.is_marking_line:
            if not self.line_start_point:
                self.line_start_point = QPointF(grid_x * self.pixel_size, grid_y * self.pixel_size)
                self.scene.addRect(
                    grid_x * self.pixel_size, grid_y * self.pixel_size,
                    self.pixel_size, self.pixel_size,
                    QPen(Qt.blue), QColor(0, 0, 255)
                )
            else:
                self.line_end_point = QPointF(grid_x * self.pixel_size, grid_y * self.pixel_size)
                self.scene.addRect(
                    grid_x * self.pixel_size, grid_y * self.pixel_size,
                    self.pixel_size, self.pixel_size,
                    QPen(Qt.blue), QColor(0, 0, 255)
                )
                self.draw_line_and_find_intersections()
                self.line_start_point = None
                self.line_end_point = None
                self.is_marking_line = False

    def mouseDoubleClickEvent(self, event):
        if self.is_drawing and len(self.polygon_points) > 2:
            first_point = self.polygon_points[0]
            last_point = self.polygon_points[-1]
            self.draw_line(last_point, first_point)
            self.is_drawing = False

    # ------------------------------------------------------------------
    # Intersections
    # ------------------------------------------------------------------

    def draw_line_and_find_intersections(self):
        if self.line_start_point and self.line_end_point:
            self.draw_line(self.line_start_point, self.line_end_point)
            intersections = self.find_intersections(self.line_start_point, self.line_end_point)
            for intersection in intersections:
                self.fill_pixel_red(
                    intersection.x() // self.pixel_size,
                    intersection.y() // self.pixel_size,
                )
            QMessageBox.information(self, "Intersections", f"Found {len(intersections)} intersections.")

    def find_intersections(self, start, end):
        intersections = []
        for i in range(len(self.polygon_points)):
            p1 = self.polygon_points[i]
            p2 = self.polygon_points[(i + 1) % len(self.polygon_points)]
            intersection = self.line_segment_intersection(start, end, p1, p2)
            if intersection:
                intersections.append(intersection)
        return intersections

    def line_segment_intersection(self, p1, p2, q1, q2):
        def det(a, b, c, d):
            return a * d - b * c

        x1, y1, x2, y2 = p1.x(), p1.y(), p2.x(), p2.y()
        x3, y3, x4, y4 = q1.x(), q1.y(), q2.x(), q2.y()

        denominator = det(x1 - x2, y1 - y2, x3 - x4, y3 - y4)
        if denominator == 0:
            return None

        px = det(det(x1, y1, x2, y2), x1 - x2, det(x3, y3, x4, y4), x3 - x4) / denominator
        py = det(det(x1, y1, x2, y2), y1 - y2, det(x3, y3, x4, y4), y3 - y4) / denominator

        if (min(x1, x2) <= px <= max(x1, x2) and
                min(y1, y2) <= py <= max(y1, y2) and
                min(x3, x4) <= px <= max(x3, x4) and
                min(y3, y4) <= py <= max(y3, y4)):
            return QPointF(px, py)
        return None

    # ------------------------------------------------------------------
    # Convexity & convex hull
    # ------------------------------------------------------------------

    def is_convex_polygon(self):
        if len(self.polygon_points) < 3:
            return False

        def cross_product_sign(p1, p2, p3):
            dx1 = p2.x() - p1.x()
            dy1 = p2.y() - p1.y()
            dx2 = p3.x() - p2.x()
            dy2 = p3.y() - p2.y()
            return dx1 * dy2 - dy1 * dx2

        signs = []
        n = len(self.polygon_points)
        for i in range(n):
            p1 = self.polygon_points[i]
            p2 = self.polygon_points[(i + 1) % n]
            p3 = self.polygon_points[(i + 2) % n]
            cross_product = cross_product_sign(p1, p2, p3)
            signs.append(cross_product > 0)

        return all(signs) or not any(signs)

    def orientation(self, p, q, r):
        return (q.y() - p.y()) * (r.x() - q.x()) - (q.x() - p.x()) * (r.y() - q.y())

    def convex_hull_graham(self):
        if len(self.polygon_points) < 3:
            QMessageBox.warning(self, "Error", "At least 3 points are required for a convex hull!")
            return []

        points = sorted(self.polygon_points, key=lambda p: (p.x(), p.y()))

        def cross(o, a, b):
            return (a.x() - o.x()) * (b.y() - o.y()) - (a.y() - o.y()) * (b.x() - o.x())

        lower = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]

    def convex_hull_jarvis(self):
        if len(self.polygon_points) < 3:
            QMessageBox.warning(self, "Error", "At least 3 points are required for a convex hull!")
            return []

        hull = []
        leftmost = min(self.polygon_points, key=lambda p: p.x())
        point_on_hull = leftmost

        while True:
            hull.append(point_on_hull)
            next_point = self.polygon_points[0]
            for p in self.polygon_points:
                if next_point == point_on_hull or \
                        (p != point_on_hull and self.orientation(point_on_hull, next_point, p) < 0):
                    next_point = p
            point_on_hull = next_point
            if point_on_hull == leftmost:
                break

        return hull

    def draw_convex_hull(self, hull):
        if not hull:
            return
        for i in range(len(hull)):
            self.draw_line(hull[i], hull[(i + 1) % len(hull)])

    # ------------------------------------------------------------------
    # Fill
    # ------------------------------------------------------------------

    def set_fill_algorithm(self, algorithm):
        self.fill_algorithm = algorithm

    def seed_fill(self, x, y):
        pass

    # ------------------------------------------------------------------
    # Normals
    # ------------------------------------------------------------------

    def _signed_area(self):
        """Signed area of the polygon (positive = CCW, negative = CW in screen coords)."""
        pts = self.polygon_points
        n = len(pts)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i].x() * pts[j].y()
            area -= pts[j].x() * pts[i].y()
        return area / 2.0

    def draw_normals(self):
        """Draw outward-facing unit normals for every edge of the closed polygon."""
        if len(self.polygon_points) < 2:
            QMessageBox.warning(self, "Normals", "Draw a polygon first!")
            return

        # Remove any previously drawn normals before redrawing
        self.hide_normals()

        # Determine winding: positive signed area means CCW (screen coords, Y-down).
        # For CCW: left-side perpendicular (-dy, dx) is outward.
        # For CW:  right-side perpendicular (dy, -dx) is outward.
        cw = self._signed_area() < 0

        pen = QPen(QColor(0, 160, 0))  # green normals
        pen.setWidth(2)

        pts = self.polygon_points
        n = len(pts)

        for i in range(n):
            p1 = pts[i]
            p2 = pts[(i + 1) % n]

            # Midpoint of the edge
            mx = (p1.x() + p2.x()) / 2.0
            my = (p1.y() + p2.y()) / 2.0

            # Edge direction
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.hypot(dx, dy)
            if length == 0:
                continue

            # Outward perpendicular (normalised)
            if cw:
                nx, ny = dy / length, -dx / length   # right-side (outward for CW)
            else:
                nx, ny = -dy / length, dx / length   # left-side (outward for CCW)

            # Arrow shaft: midpoint → tip
            tx = mx + nx * NORMAL_LENGTH
            ty = my + ny * NORMAL_LENGTH
            shaft = self.scene.addLine(mx, my, tx, ty, pen)
            self._normal_items.append(shaft)

            # Arrowhead: two short lines rotated ±ARROW_ANGLE from the back direction
            back_angle = math.atan2(-ny, -nx)
            for sign in (+1, -1):
                angle = back_angle + sign * math.radians(ARROW_ANGLE)
                ax = tx + math.cos(angle) * ARROW_SIZE
                ay = ty + math.sin(angle) * ARROW_SIZE
                arm = self.scene.addLine(tx, ty, ax, ay, pen)
                self._normal_items.append(arm)

    def hide_normals(self):
        """Remove all normal arrows from the scene."""
        for item in self._normal_items:
            self.scene.removeItem(item)
        self._normal_items = []


# ======================================================================
# Dialog / UI
# ======================================================================

class ViewerWithPolygonMenu(QDialog):
    def _create_drawer(self, pixel_size):
        return PolygonDrawer(pixel_size)

    def __init__(self, pixel_size=10):
        super().__init__()
        self.setWindowTitle("Polygon Drawer")

        layout = QHBoxLayout()

        self.polygon_drawer = self._create_drawer(pixel_size)

        self.button_layout = QVBoxLayout()

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.polygon_drawer.reset)
        self.button_layout.addWidget(self.reset_button)

        self.algorithm_selector = QComboBox()
        self.algorithm_selector.addItems(["Bresenham", "CDA", "Wu"])
        self.algorithm_selector.currentTextChanged.connect(
            self.polygon_drawer.set_line_algorithm
        )
        self.button_layout.addWidget(self.algorithm_selector)

        self.convexity_button = QPushButton("Check Convexity")
        self.convexity_button.clicked.connect(self.check_convexity)
        self.button_layout.addWidget(self.convexity_button)

        self.hull_button = QPushButton("Build Convex Hull")
        self.hull_button.clicked.connect(self.build_convex_hull)
        self.button_layout.addWidget(self.hull_button)

        self.intersection_button = QPushButton("Find Intersections")
        self.intersection_button.clicked.connect(self.start_marking_line)
        self.button_layout.addWidget(self.intersection_button)

        # --- Normal buttons ---
        self.show_normals_button = QPushButton("Show Normals")
        self.show_normals_button.clicked.connect(self.polygon_drawer.draw_normals)
        self.button_layout.addWidget(self.show_normals_button)

        self.hide_normals_button = QPushButton("Hide Normals")
        self.hide_normals_button.clicked.connect(self.polygon_drawer.hide_normals)
        self.button_layout.addWidget(self.hide_normals_button)
        # ----------------------

        self.debug_checkbox = QCheckBox("Debug Mode")
        self.debug_checkbox.stateChanged.connect(self.polygon_drawer.toggle_debug_mode)
        self.button_layout.addWidget(self.debug_checkbox)

        self.button_layout.addStretch()
        layout.addLayout(self.button_layout)
        layout.addWidget(self.polygon_drawer)

        self.setLayout(layout)

    def toggle_debug_mode(self, state):
        self.polygon_drawer.debug_mode = state == Qt.Checked

    def start_marking_line(self):
        self.polygon_drawer.is_marking_line = True
        self.polygon_drawer.is_drawing = False
        QMessageBox.information(self, "Mark Points", "Click on the scene to mark two points for the line.")

    def build_convex_hull(self):
        method, ok = QInputDialog.getItem(
            self,
            "Select Method",
            "Choose a method to construct the convex hull:",
            ["Graham's Scan", "Jarvis March"],
            0,
            False,
        )

        if not ok:
            return

        if method == "Graham's Scan":
            hull = self.polygon_drawer.convex_hull_graham()
        elif method == "Jarvis March":
            hull = self.polygon_drawer.convex_hull_jarvis()
        else:
            return

        self.polygon_drawer.scene.clear()
        self.polygon_drawer.draw_grid()

        for point in self.polygon_drawer.polygon_points:
            self.polygon_drawer.scene.addRect(
                point.x(), point.y(),
                self.polygon_drawer.pixel_size, self.polygon_drawer.pixel_size,
                QPen(Qt.black), QColor(100, 0, 0)
            )

        self.polygon_drawer.draw_convex_hull(hull)

    def check_convexity(self):
        is_convex = self.polygon_drawer.is_convex_polygon()
        message = "The polygon is convex!" if is_convex else "The polygon is not convex!"
        QMessageBox.information(self, "Convexity Check", message)

    def start_seed_fill(self):
        algorithms = ["Ordered Edge List", "Active Edge List", "Simple Seed Fill", "Scanline Seed Fill"]
        algorithm, ok = QInputDialog.getItem(
            self,
            "Choose Fill Algorithm",
            "Select an algorithm:",
            algorithms,
            0,
            False,
        )
        if ok:
            self.polygon_drawer.set_fill_algorithm(algorithm)
            self.polygon_drawer.start_seed_selection()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ViewerWithPolygonMenu(pixel_size=10)
    viewer.show()
    sys.exit(app.exec_())