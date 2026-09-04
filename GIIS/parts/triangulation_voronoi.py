import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsView,
                             QGraphicsScene, QVBoxLayout, QFrame, QPushButton,
                             QHBoxLayout, QDialog, QLabel)
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QPolygonF

_INSIDE, _LEFT, _RIGHT, _BOTTOM, _TOP = 0, 1, 2, 4, 8

def _compute_outcode(x, y, x_min, y_min, x_max, y_max):
    code = _INSIDE
    if   x < x_min: code |= _LEFT
    elif x > x_max: code |= _RIGHT
    if   y < y_min: code |= _TOP
    elif y > y_max: code |= _BOTTOM
    return code

def _clip_segment(x0, y0, x1, y1, bounds):
    x_min, y_min, x_max, y_max = bounds
    code0 = _compute_outcode(x0, y0, x_min, y_min, x_max, y_max)
    code1 = _compute_outcode(x1, y1, x_min, y_min, x_max, y_max)
    while True:
        if not (code0 | code1):
            return (x0, y0), (x1, y1)
        if code0 & code1:
            return None
        code_out = code0 if code0 else code1
        dx = x1 - x0
        dy = y1 - y0
        if code_out & _BOTTOM:
            x = x0 + dx * (y_max - y0) / dy if dy else x0
            y = y_max
        elif code_out & _TOP:
            x = x0 + dx * (y_min - y0) / dy if dy else x0
            y = y_min
        elif code_out & _RIGHT:
            y = y0 + dy * (x_max - x0) / dx if dx else y0
            x = x_max
        else:
            y = y0 + dy * (x_min - x0) / dx if dx else y0
            x = x_min
        if code_out == code0:
            x0, y0 = x, y
            code0 = _compute_outcode(x0, y0, x_min, y_min, x_max, y_max)
        else:
            x1, y1 = x, y
            code1 = _compute_outcode(x1, y1, x_min, y_min, x_max, y_max)

def _is_finite(x, y):
    return abs(x) < 1e9 and abs(y) < 1e9

class DelaunayTriangulation:
    def __init__(self, points):
        self.points = points
        self.triangles = []
        self._create_super_triangle()
        for point in points:
            self._add_point(point)
        self._remove_super_triangle()

    def _create_super_triangle(self):
        min_x = min(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_x = max(p.x() for p in self.points)
        max_y = max(p.y() for p in self.points)

        width  = max_x - min_x
        height = max_y - min_y

        p1 = QPointF(min_x - width,     min_y - height * 2)
        p2 = QPointF(max_x + width,     min_y - height * 2)
        p3 = QPointF(min_x + width / 2, max_y + height * 2)

        self.super_triangle = (p1, p2, p3)
        self.triangles.append((p1, p2, p3))

    def _add_point(self, point):
        bad_triangles = []
        for triangle in self.triangles:
            if self._is_point_in_circumcircle(point, triangle):
                bad_triangles.append(triangle)

        polygon = []
        for triangle in bad_triangles:
            for i in range(3):
                edge = (triangle[i], triangle[(i + 1) % 3])
                is_shared = False
                for other_triangle in bad_triangles:
                    if triangle == other_triangle:
                        continue
                    for j in range(3):
                        other_edge = (other_triangle[j], other_triangle[(j + 1) % 3])
                        if edge[0] == other_edge[1] and edge[1] == other_edge[0]:
                            is_shared = True
                            break
                if not is_shared:
                    polygon.append(edge)

        for triangle in bad_triangles:
            self.triangles.remove(triangle)

        for edge in polygon:
            self.triangles.append((edge[0], edge[1], point))

    def _remove_super_triangle(self):
        p1, p2, p3 = self.super_triangle
        self.triangles = [
            t for t in self.triangles
            if p1 not in t and p2 not in t and p3 not in t
        ]

    def _is_point_in_circumcircle(self, point, triangle):
        a, b, c = triangle
        ax, ay = a.x(), a.y()
        bx, by = b.x(), b.y()
        cx, cy = c.x(), c.y()
        px, py = point.x(), point.y()

        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if d == 0:
            return False

        ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d

        radius_sq = (ax - ux)**2 + (ay - uy)**2
        dist_sq   = (px - ux)**2 + (py - uy)**2
        return dist_sq <= radius_sq

    def compute_voronoi(self, bounds=None):
        voronoi_edges = []
        circumcenters = {}

        for triangle in self.triangles:
            key = tuple((p.x(), p.y()) for p in triangle)
            cx, cy = self._compute_circumcenter(triangle)
            circumcenters[key] = (cx, cy)

        BIG = 1e5
        seen_inner = set()

        for triangle in self.triangles:
            key = tuple((p.x(), p.y()) for p in triangle)
            cx, cy = circumcenters[key]
            if not _is_finite(cx, cy):
                continue

            for i in range(3):
                neighbor = self._find_neighbor(triangle, i)
                if neighbor:
                    neighbor_key = tuple((p.x(), p.y()) for p in neighbor)
                    nx, ny = circumcenters[neighbor_key]
                    if not _is_finite(nx, ny):
                        continue
                    edge_id = tuple(sorted([key, neighbor_key]))
                    if edge_id in seen_inner:
                        continue
                    seen_inner.add(edge_id)

                    if bounds:
                        seg = _clip_segment(cx, cy, nx, ny, bounds)
                        if seg:
                            voronoi_edges.append((QPointF(*seg[0]), QPointF(*seg[1])))
                    else:
                        voronoi_edges.append((QPointF(cx, cy), QPointF(nx, ny)))
                else:
                    # граничное ребро: перпендикуляр к ребру треугольника
                    p1 = triangle[i]
                    p2 = triangle[(i + 1) % 3]
                    p3 = triangle[(i + 2) % 3]  # противолежащая вершина

                    # вектор вдоль ребра p1→p2
                    ex = p2.x() - p1.x()
                    ey = p2.y() - p1.y()
                    length = (ex*ex + ey*ey) ** 0.5
                    if length < 1e-10:
                        continue
                    # перпендикуляр (два варианта: влево и вправо от ребра)
                    px, py = -ey / length, ex / length

                    mx = (p1.x() + p2.x()) / 2
                    my = (p1.y() + p2.y()) / 2
                    # вектор от midpoint к p3
                    tx = p3.x() - mx
                    ty = p3.y() - my
                    # если перпендикуляр смотрит в сторону p3 — разворачиваем
                    if px * tx + py * ty > 0:
                        px, py = -px, -py

                    rx2, ry2 = cx + px * BIG, cy + py * BIG
                    if bounds:
                        seg = _clip_segment(cx, cy, rx2, ry2, bounds)
                        if seg:
                            voronoi_edges.append((QPointF(*seg[0]), QPointF(*seg[1])))

        return voronoi_edges

    def _compute_circumcenter(self, triangle):
        a, b, c = triangle
        ax, ay = a.x(), a.y()
        bx, by = b.x(), b.y()
        cx, cy = c.x(), c.y()

        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if d == 0:
            return float('inf'), float('inf')

        ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
        return ux, uy

    def _find_neighbor(self, triangle, edge_index):
        edge = (triangle[edge_index], triangle[(edge_index + 1) % 3])
        for other in self.triangles:
            if other == triangle:
                continue
            for i in range(3):
                other_edge = (other[i], other[(i + 1) % 3])
                if edge[0] == other_edge[1] and edge[1] == other_edge[0]:
                    return other
        return None

class DelaunayTriangulationView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setFrameShape(QFrame.NoFrame)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.points    = []
        self.triangles = []

        self.setMouseTracking(True)
        self.setInteractive(True)

        self.point_pen      = QPen(Qt.red, 3)
        self.point_brush    = QBrush(Qt.red)
        self.triangle_pen   = QPen(Qt.blue, 1)
        self.triangle_brush = QBrush(QColor(220, 200, 255, 100))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.points.append(QPointF(scene_pos.x(), scene_pos.y()))
            self.update_triangulation()
            self.draw_scene()

    def update_triangulation(self):
        if len(self.points) < 3:
            self.triangles = []
            return
        self.triangles = DelaunayTriangulation([QPointF(p) for p in self.points]).triangles

    def draw_scene(self):
        self.scene.clear()
        for triangle in self.triangles:
            polygon = QPolygonF()
            for point in triangle:
                polygon.append(point)
            self.scene.addPolygon(polygon, self.triangle_pen, self.triangle_brush)
        for point in self.points:
            self.scene.addEllipse(point.x() - 3, point.y() - 3, 6, 6,
                                  self.point_pen, self.point_brush)

    def clear_points(self):
        self.points    = []
        self.triangles = []
        self.scene.clear()


class DelaunayViewer(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delaunay Triangulation")

        self.delaunay_view = DelaunayTriangulationView()

        clear_button = QPushButton("Clear Points")
        clear_button.clicked.connect(self.delaunay_view.clear_points)

        button_layout = QVBoxLayout()
        button_layout.addWidget(clear_button)
        button_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.delaunay_view)
        self.setLayout(main_layout)

class VoronoiDiagramView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setFrameShape(QFrame.NoFrame)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.points        = []
        self.voronoi_edges = []

        self.point_pen   = QPen(Qt.red, 3)
        self.point_brush = QBrush(Qt.red)
        self.edge_pen    = QPen(Qt.blue, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.points.append(QPointF(scene_pos.x(), scene_pos.y()))
            self.update_voronoi()
            self.draw_scene()

    def update_voronoi(self):
        if len(self.points) < 3:
            self.voronoi_edges = []
            return
        r = self.scene.sceneRect()
        bounds = (r.x(), r.y(), r.x() + r.width(), r.y() + r.height())
        triangulation = DelaunayTriangulation(self.points)
        self.voronoi_edges = triangulation.compute_voronoi(bounds=bounds)

    def draw_scene(self):
        self.scene.clear()
        for edge in self.voronoi_edges:
            self.scene.addLine(edge[0].x(), edge[0].y(),
                               edge[1].x(), edge[1].y(), self.edge_pen)
        for point in self.points:
            self.scene.addEllipse(point.x() - 3, point.y() - 3, 6, 6,
                                  self.point_pen, self.point_brush)

    def clear_points(self):
        self.points        = []
        self.voronoi_edges = []
        self.scene.clear()
        self.update()


class VoronoiViewer(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voronoi Diagram")

        self.voronoi_view = VoronoiDiagramView()

        clear_button = QPushButton("Clear Points")
        clear_button.clicked.connect(self.voronoi_view.clear_points)

        button_layout = QVBoxLayout()
        button_layout.addWidget(clear_button)
        button_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.voronoi_view)
        self.setLayout(main_layout)

class TriangulationVoronoiDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Algorithm")
        self.setGeometry(130, 120, 300, 150)
        self._choice = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choose a mode:"))

        tri_btn = QPushButton("Delaunay Triangulation")
        tri_btn.clicked.connect(lambda: self._select("triangulation"))
        layout.addWidget(tri_btn)

        vor_btn = QPushButton("Voronoi Diagram")
        vor_btn.clicked.connect(lambda: self._select("voronoi"))
        layout.addWidget(vor_btn)

        self.setLayout(layout)

    def _select(self, choice):
        self._choice = choice
        self.accept()

    def get_selection(self):
        return self._choice


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TriangulationVoronoiDialog()
    if dialog.exec_() == QDialog.Accepted:
        choice = dialog.get_selection()
        if choice == "triangulation":
            window = DelaunayViewer()
        else:
            window = VoronoiViewer()
        window.show()
        sys.exit(app.exec_())