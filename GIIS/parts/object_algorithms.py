import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QGraphicsView,
    QGraphicsScene, QHBoxLayout, QLineEdit, QFormLayout, QSpinBox, QDoubleSpinBox
)


class InputDialog(QDialog):
    def __init__(self, title, inputs):
        super().__init__()
        self.setWindowTitle(title)

        self.inputs = {}

        layout = QFormLayout()
        for label, input_type in inputs.items():
            if input_type == 'float':
                input_field = QDoubleSpinBox()
                input_field.setRange(-1000.0, 1000.0)
                input_field.setDecimals(2)
                input_field.setValue(0.0)
            elif input_type == 'int':
                input_field = QSpinBox()
                input_field.setRange(-360, 360)
                input_field.setValue(0)
            else:
                input_field = QLineEdit()

            self.inputs[label] = input_field
            layout.addRow(label, input_field)

        self.setLayout(layout)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

    def get_inputs(self):
        return {label: field.value() if isinstance(field, (QDoubleSpinBox, QSpinBox)) else field.text()
                for label, field in self.inputs.items()}


class Object3DViewerDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Object to View")
        self.setGeometry(130, 120, 300, 200)

        layout = QVBoxLayout()
        self.label = QLabel("Choose an object to load:")
        layout.addWidget(self.label)

        self.cube_button = QPushButton("Cube")
        self.cube_button.setCheckable(True)
        self.cube_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.cube_button)

        self.pyramid_button = QPushButton("Pyramid")
        self.pyramid_button.setCheckable(True)
        self.pyramid_button.clicked.connect(self.on_button_click)
        layout.addWidget(self.pyramid_button)

        layout.addStretch()

        self.load_button = QPushButton("Load Object")
        self.load_button.clicked.connect(self.accept)
        layout.addWidget(self.load_button)

        self.setLayout(layout)

    def on_button_click(self):
        sender = self.sender()
        if sender.isChecked():
            for button in (self.cube_button, self.pyramid_button):
                if button != sender:
                    button.setChecked(False)

    def get_selection(self):
        if self.cube_button.isChecked():
            return "cube.txt"
        elif self.pyramid_button.isChecked():
            return "pyramid.txt"
        return None


class Object3DViewer(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.setScene(self.scene)

        self.vertices = []
        self.edges = []

        self.projection_type = "perspective"

        theta_x = np.radians(30)
        theta_y = np.radians(45)

        rotation_matrix_x = np.array([[1, 0, 0, 0],
                                      [0, np.cos(theta_x), -np.sin(theta_x), 0],
                                      [0, np.sin(theta_x), np.cos(theta_x), 0],
                                      [0, 0, 0, 1]])

        rotation_matrix_y = np.array([[np.cos(theta_y), 0, np.sin(theta_y), 0],
                                      [0, 1, 0, 0],
                                      [-np.sin(theta_y), 0, np.cos(theta_y), 0],
                                      [0, 0, 0, 1]])

        self.transform_matrix = rotation_matrix_x @ rotation_matrix_y
        self.pixel_size = 1
        self.projection_matrix = self.create_projection_matrix()
        self.draw_object()

    def create_projection_matrix(self, fov=110, aspect=800 / 600, near=0.1, far=100):
        """Creates a perspective projection matrix."""
        fov_rad = 1 / np.tan(np.radians(fov) / 2)
        z_range = near - far
        return np.array([
            [fov_rad / aspect, 0, 0, 0],
            [0, fov_rad, 0, 0],
            [0, 0, (far + near) / z_range, (2 * far * near) / z_range],
            [0, 0, -1, 0]
        ])

    def create_orthographic_matrix(self, left=-1, right=1, bottom=-1, top=1, near=-1, far=1):
        """Creates an orthographic projection matrix."""
        return np.array([
            [2 / (right - left), 0, 0, -(right + left) / (right - left)],
            [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
            [0, 0, 2 / (near - far), -(far + near) / (far - near)],
            [0, 0, 0, 1]
        ])

    def toggle_projection(self):
        """Toggles between perspective and orthographic projection."""
        if self.projection_type == "perspective":
            self.projection_type = "orthographic"
            self.projection_matrix = self.create_orthographic_matrix(left=-1.5, right=1.5, bottom=-1.5, top=1.5,
                                                                     near=-2, far=2)
        else:
            self.projection_type = "perspective"
            self.projection_matrix = self.create_projection_matrix()
        self.draw_object()

    def load_object(self, filename):
        """Loads a 3D object from a file."""
        try:
            with open(filename, "r") as file:
                lines = file.readlines()
                for line in lines:
                    parts = line.split()
                    if not parts:
                        continue
                    if parts[0] == "v":
                        self.vertices.append([float(parts[1]), float(parts[2]), float(parts[3]), 1.0])
                    elif parts[0] == "e":
                        self.edges.append((int(parts[1]), int(parts[2])))
        except FileNotFoundError:
            print(f"File {filename} not found.")
            # sys.exit(1)

    def draw_axes(self):
        pass

    def draw_object(self):
        self.scene.clear()
        self.draw_axes()
        projected_vertices = []

        for vertex in self.vertices:
            transformed_vertex = self.transform_matrix @ vertex
            projected_vertex = self.projection_matrix @ transformed_vertex
            if projected_vertex[3] != 0:
                projected_vertex /= projected_vertex[3]
            projected_vertices.append(projected_vertex)

        for edge in self.edges:
            v1 = projected_vertices[edge[0]]
            v2 = projected_vertices[edge[1]]
            self.draw_line(v1[:2], v2[:2])

    def draw_line(self, p1, p2):
        """Draws a line between two 2D points."""
        x1, y1 = int(p1[0] * 400 + 400), int(-p1[1] * 300 + 300)
        x2, y2 = int(p2[0] * 400 + 400), int(-p2[1] * 300 + 300)
        self.scene.addLine(x1, y1, x2, y2, QPen(QColor(0, 0, 0)))

    def keyPressEvent(self, event):
        """Handles keyboard input for transformations."""
        key = event.key()
        if key == Qt.Key_W:
            self.translatew(0, 0.1, 0)
        elif key == Qt.Key_Q:
            self.translatew(0, -0.1, 0)
        elif key == Qt.Key_A:
            self.translatew(-0.1, 0, 0)
        elif key == Qt.Key_S:
            self.translatew(0.1, 0, 0)
        elif key == Qt.Key_Z:
            self.translatew(0, 0, -0.1)
        elif key == Qt.Key_X:
            self.translatew(0, 0, 0.1)
        elif key == Qt.Key_I:
            self.rotatew(5, axis="y")
        elif key == Qt.Key_O:
            self.rotatew(-5, axis="y")
        elif key == Qt.Key_K:
            self.rotatew(5, axis="x")
        elif key == Qt.Key_L:
            self.rotatew(-5, axis="x")
        elif key == Qt.Key_M:
            self.rotatew(5, axis="z")
        elif key == Qt.Key_Comma:
            self.rotatew(-5, axis="z")
        elif key == Qt.Key_R:
            self.scalew(2)
        elif key == Qt.Key_F:
            self.scalew(0.5)
        self.draw_object()

    def translatew(self, dx, dy, dz):

        translation_matrix = np.eye(4)
        translation_matrix[0, 3] = dx
        translation_matrix[1, 3] = dy
        translation_matrix[2, 3] = dz
        self.transform_matrix = self.transform_matrix @ translation_matrix

        print("translation_matrix applied:")
        print(translation_matrix)
        print("Updated transformation matrix:")
        print(self.transform_matrix)

    def rotatew(self, angle, axis="x"):
        angle_rad = np.radians(angle)
        rotation_matrix = np.eye(4)

        if axis == "x":
            rotation_matrix[1, 1] = np.cos(angle_rad)
            rotation_matrix[1, 2] = -np.sin(angle_rad)
            rotation_matrix[2, 1] = np.sin(angle_rad)
            rotation_matrix[2, 2] = np.cos(angle_rad)
        elif axis == "y":
            rotation_matrix[0, 0] = np.cos(angle_rad)
            rotation_matrix[0, 2] = np.sin(angle_rad)
            rotation_matrix[2, 0] = -np.sin(angle_rad)
            rotation_matrix[2, 2] = np.cos(angle_rad)
        elif axis == "z":
            rotation_matrix[0, 0] = np.cos(angle_rad)
            rotation_matrix[0, 1] = -np.sin(angle_rad)
            rotation_matrix[1, 0] = np.sin(angle_rad)
            rotation_matrix[1, 1] = np.cos(angle_rad)

        self.transform_matrix = rotation_matrix @ self.transform_matrix

    def scalew(self, factor):
        """Applies a uniform scaling transformation."""
        if factor <= 0:
            print("Scaling factor must be greater than 0.")
            return

        scaling_matrix = np.eye(4)
        scaling_matrix[0, 0] = factor
        scaling_matrix[1, 1] = factor
        scaling_matrix[2, 2] = factor

        translation = self.transform_matrix[:3, 3]

        self.transform_matrix[:3, 3] = [0, 0, 0]

        self.transform_matrix = self.transform_matrix @ scaling_matrix

        self.transform_matrix[:3, 3] = translation * factor

        print("Scaling matrix applied:")
        print(scaling_matrix)
        print("Updated transformation matrix:")
        print(self.transform_matrix)

    def reflectw(self, axis="x"):
        """Applies a reflection transformation along the specified axis."""
        reflection_matrix = np.eye(4)

        if axis == "x":
            reflection_matrix[0, 0] = -1
        elif axis == "y":
            reflection_matrix[1, 1] = -1
        elif axis == "z":
            reflection_matrix[2, 2] = -1
        else:
            print("Invalid axis. Please choose 'x', 'y', or 'z'.")
            return

        self.transform_matrix = reflection_matrix @ self.transform_matrix

        print("Reflection matrix applied:")
        print(reflection_matrix)
        print("Updated transformation matrix:")
        print(self.transform_matrix)


class ViewerWithMenu(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Object Viewer")

        layout = QHBoxLayout()

        self.viewer = Object3DViewer()

        button_layout = QVBoxLayout()

        self.translate_button = QPushButton("Translate")
        self.translate_button.clicked.connect(self.translate)
        button_layout.addWidget(self.translate_button)

        self.rotate_button = QPushButton("Rotate")
        self.rotate_button.clicked.connect(self.rotate)
        button_layout.addWidget(self.rotate_button)

        self.scale_button = QPushButton("Scale")
        self.scale_button.clicked.connect(self.scale)
        button_layout.addWidget(self.scale_button)

        self.reflect_button = QPushButton("Reflect")
        self.reflect_button.clicked.connect(self.reflect)
        button_layout.addWidget(self.reflect_button)

        self.projection_button = QPushButton("Toggle Projection")
        self.projection_button.clicked.connect(self.viewer.toggle_projection)
        button_layout.addWidget(self.projection_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_object)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addWidget(self.viewer)

        self.setLayout(layout)

    def translate(self):
        dialog = InputDialog("Translate", {"dx": "float", "dy": "float", "dz": "float"})
        if dialog.exec_() == QDialog.Accepted:
            inputs = dialog.get_inputs()
            self.viewer.translatew(inputs["dx"], inputs["dy"], inputs["dz"])
            self.viewer.draw_object()

    def reflect(self):
        """Opens a dialog to specify the axis of reflection."""
        dialog = InputDialog("Reflect", {"axis (x/y/z)": "str"})
        if dialog.exec_() == QDialog.Accepted:
            inputs = dialog.get_inputs()
            axis = inputs["axis (x/y/z)"].lower()
            if axis in ["x", "y", "z"]:
                self.viewer.reflectw(axis)
                self.viewer.draw_object()
            else:
                print("Invalid axis. Please enter 'x', 'y', or 'z'.")

    def rotate(self):
        dialog = InputDialog("Rotate", {"angle": "int", "axis (x/y/z)": "str"})
        if dialog.exec_() == QDialog.Accepted:
            inputs = dialog.get_inputs()
            self.viewer.rotatew(inputs["angle"], axis=inputs["axis (x/y/z)"].lower())
            self.viewer.draw_object()

    def scale(self):
        dialog = InputDialog("Scale", {"factor": "float"})
        if dialog.exec_() == QDialog.Accepted:
            inputs = dialog.get_inputs()
            self.viewer.scalew(inputs["factor"])
            self.viewer.draw_object()

    def reset_object(self):
        """Resets the object to its initial state."""
        theta_x = np.radians(30)
        theta_y = np.radians(45)

        rotation_matrix_x = np.array([[1, 0, 0, 0],
                                      [0, np.cos(theta_x), -np.sin(theta_x), 0],
                                      [0, np.sin(theta_x), np.cos(theta_x), 0],
                                      [0, 0, 0, 1]])

        rotation_matrix_y = np.array([[np.cos(theta_y), 0, np.sin(theta_y), 0],
                                      [0, 1, 0, 0],
                                      [-np.sin(theta_y), 0, np.cos(theta_y), 0],
                                      [0, 0, 0, 1]])
        self.viewer.transform_matrix = rotation_matrix_x @ rotation_matrix_y
        self.viewer.draw_object()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = Object3DViewerDialog()
    if dialog.exec_() == QDialog.Accepted:
        object_file = dialog.get_selection()
        if object_file:
            viewer = Object3DViewer()
            viewer.load_object(object_file)
            viewer.show()
            sys.exit(app.exec_())