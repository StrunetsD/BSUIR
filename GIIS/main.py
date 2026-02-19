import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QDialog, QLabel, QToolBar
from PyQt5.QtCore import Qt

from algo.line import LineDrawingArea, LineAlgorithmDialog
from algo.circle import CircleDrawingArea, CircleAlgorithmDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Graphic Editor")
        self.setGeometry(100, 100, 1300, 950)

        self.drawing_area = LineDrawingArea()
        self.drawing_area.draw_grid()
        self.setCentralWidget(self.drawing_area)

        self.create_menu()
        self.create_toolbar()

        self.overlay_label = QLabel(self)
        self.overlay_label.setGeometry(1000, 20, 280, 100)
        self.overlay_label.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.overlay_label.setWordWrap(True)
        self.setStyleSheet("""
                QMenuBar {
                    background-color: #2E3604;
                    color: white;
                }

                QMenuBar::item:selected {
                    background-color: #4E5E07;
                }

                QToolBar {
                    background-color: #536e3b;
                    border-bottom: 2px solid #899f75;
                }

                QToolButton {
                    background-color: transparent;
                    color: white;
                    padding: 6px 10px;
                }

                QToolButton:hover {
                    background-color: #4E5E07;
                },

                QToolButton:pressed {
                    background-color: #6E7E0A;
                }
                """)
        self.overlay_label.setVisible(False)

    def clear_canvas(self):
        if self.drawing_area:
            self.drawing_area.scene.clear()
            self.drawing_area.draw_grid()

    def create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Menu")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        clear_action = QAction("Clear canvas", self)
        clear_action.triggered.connect(self.clear_canvas)
        file_menu.addAction(clear_action)

    def create_toolbar(self):
        toolbar = QToolBar("Drawing Tools")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        line_action = QAction("Lab 1 - Lines", self)
        line_action.triggered.connect(self.show_algorithm_dialog)
        toolbar.addAction(line_action)

        circle_action = QAction("Lab 2 - Circles", self)
        circle_action.triggered.connect(self.show_circle_algorithm_dialog)
        toolbar.addAction(circle_action)

    def show_algorithm_dialog(self):
        dialog = LineAlgorithmDialog()
        if dialog.exec_() == QDialog.Accepted:
            algorithm, debug_mode, clear_canvas, coordinates = dialog.get_selection()
            if algorithm:
                self.drawing_area = LineDrawingArea()
                self.setCentralWidget(self.drawing_area)
                self.drawing_area.draw_grid()
                self.drawing_area.set_algorithm(algorithm, debug_mode, clear_canvas, coordinates)
                self.update_overlay_label(algorithm, debug_mode, clear_canvas, "Lines")
                self.overlay_label.raise_()

    def show_circle_algorithm_dialog(self):
        dialog = CircleAlgorithmDialog()
        if dialog.exec_() == QDialog.Accepted:
            curve, debug_mode, clear_canvas = dialog.get_selection()
            if curve:
                self.drawing_area = CircleDrawingArea()
                self.drawing_area.draw_grid()
                self.setCentralWidget(self.drawing_area)
                self.drawing_area.set_algorithm(curve, debug_mode, clear_canvas)
                self.update_overlay_label(curve, debug_mode, clear_canvas, "Second-Order Curves")
                self.overlay_label.raise_()

    def update_overlay_label(self, algorithm, debug_mode, clear_canvas, mode):
        debug_status = "ON" if debug_mode else "OFF"
        clear_status = "ON" if clear_canvas else "OFF"

        self.overlay_label.setText(
            f"Algorithm: {algorithm}\n"
            f"Debug Mode: {debug_status}\n"
            f"Clear Canvas: {clear_status}\n"
            f"Mode: {mode}"
        )
        self.overlay_label.setVisible(True)
        self.overlay_label.raise_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())