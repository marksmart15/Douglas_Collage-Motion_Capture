import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QComboBox, QLineEdit, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, pyqtSignal


class PointSelectorApp(QMainWindow):
    DistanceChanged = pyqtSignal(float)
    unitChanged = pyqtSignal(str)
    
    def __init__(self, camera_index=1, measurement_unit="cm"):
        super(PointSelectorApp, self).__init__()

        self.cap = cv2.VideoCapture(camera_index)
        self.points = []
        self.dragging_point = None
        self.measurement_unit = measurement_unit
        self.window_name = 'Webcam Point Selector'

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.image_label = QLabel()
        self.finish_button = QPushButton('Finish')
        self.unit_combobox = QComboBox()
        self.unit_combobox.addItems(["cm", "inch"])
        self.unit_combobox.setCurrentText(self.measurement_unit)
        self.distance_input = QLineEdit()

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Adjust the interval based on your needs

    def setup_ui(self):
        layout = QVBoxLayout()

        # Image label
        layout.addWidget(self.image_label)

        # Entry box
        entry_layout = QHBoxLayout()
        entry_layout.addWidget(self.distance_input)
        entry_layout.addWidget(self.unit_combobox)
        layout.addLayout(entry_layout)

        # Finish button
        layout.addWidget(self.finish_button)

        self.central_widget.setLayout(layout)

        self.finish_button.clicked.connect(self.on_finish_button_clicked)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.draw_points(frame)
            image = self.convert_frame_to_qimage(frame)
            self.image_label.setPixmap(QPixmap.fromImage(image))

    def convert_frame_to_qimage(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return q_image.rgbSwapped()

    def draw_points(self, frame):
        dot_size = 2  # Adjust the dot size if needed
        for point in self.points:
            cv2.circle(frame, point, dot_size, (0, 255, 0), -1)

    def mousePressEvent(self, event):
        if event.button() == 1:  # Left mouse button
            self.dragging_point = None
            for i, point in enumerate(self.points):
                distance = np.sqrt((point[0] - (event.x() - 10)) ** 2 + (point[1] - (event.y() - 10)) ** 2)
                if distance < 10:
                    self.dragging_point = i
                    break
            if self.dragging_point is None:
                if len(self.points) < 2:
                    self.points.append((event.x()-10, event.y()-10))

    def mouseMoveEvent(self, event):
        if self.dragging_point is not None:
            self.points[self.dragging_point] = (event.x() - 10, event.y()- 10)

    def mouseReleaseEvent(self, event):
        self.dragging_point = None

    def on_finish_button_clicked(self):
        if len(self.points) == 2:
            result = self.calculate_distance_percentage()
            if result is not None:
                percentage, unit = result
                self.DistanceChanged.emit(percentage)
                self.unitChanged.emit(unit)
        else:
            print("Please select two points.")

    def calculate_distance_percentage(self):
        ret, frame = self.cap.read()
        if ret:
            height, width, _ = frame.shape
            if len(self.points) == 2:
                distance = np.sqrt((self.points[1][0] - self.points[0][0]) ** 2 + (self.points[1][1] - self.points[0][1]) ** 2)
                percentage = (distance / np.sqrt(width ** 2 + height ** 2)) * 100
                unit = self.unit_combobox.currentText()
                return percentage, unit
        return None
    
    def get_distances_and_unit(self):
        distance_percentage = self.calculate_distance_percentages()
        unit = self.unit_combobox.currentText()
        return distance_percentage, unit
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PointSelectorApp(camera_index=1)
    window.show()
    sys.exit(app.exec_())
