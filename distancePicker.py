import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QComboBox, QLineEdit, QHBoxLayout, QErrorMessage, QDesktopWidget, QSizePolicy 
from PyQt5.QtGui import QImage, QPixmap, QIntValidator
from PyQt5.QtCore import QTimer, pyqtSignal, Qt

class PointSelectorApp(QMainWindow):
    DistanceChanged = pyqtSignal(float)
    DistanceUser = pyqtSignal(float)
    unitChanged = pyqtSignal(str)
    
    def __init__(self, camera_index, measurement_unit="cm"):
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

        # Set the initial window size to be half the size of the screen
        screen_geometry = QDesktopWidget().screenGeometry()
        self.resize(screen_geometry.width() // 2, screen_geometry.height() // 2)
        

    def setup_ui(self):
        layout = QVBoxLayout()

        # Image label
        layout.addWidget(self.image_label)

        # Entry box and drop-down menu layout
        entry_layout = QHBoxLayout()

        # Set up a validator for integers only
        int_validator = QIntValidator()
        self.distance_input.setValidator(int_validator)

        # Set the default value to "100"
        self.distance_input.setText("100")

        # Set maximum width for the QLineEdit
        self.distance_input.setMaximumWidth(50)  # Adjust the width as needed

        # Center the QLineEdit and QComboBox in the layout
        entry_layout.addStretch()
        entry_layout.addWidget(self.distance_input, alignment=Qt.AlignCenter)
        entry_layout.addWidget(self.unit_combobox, alignment=Qt.AlignCenter)
        entry_layout.addStretch()

        layout.addLayout(entry_layout)

        # Smaller and centered finish button
        self.finish_button.setMaximumWidth(50)  # Adjust the width as needed
        layout.addWidget(self.finish_button, alignment=Qt.AlignCenter)

        self.central_widget.setLayout(layout)

        self.finish_button.clicked.connect(self.on_finish_button_clicked)
        
    def resizeEvent(self, event):
        # Call the base class resizeEvent method
        super(PointSelectorApp, self).resizeEvent(event)
        
        # Update the frame size when the window is resized
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Resize the frame to fit the window while maintaining the aspect ratio
            aspect_ratio = frame.shape[1] / frame.shape[0]
            new_width = self.image_label.width()
            new_height = int(new_width / aspect_ratio)
            frame = cv2.resize(frame, (new_width, new_height))
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
            #print("y = ", event.y(), " x =", event.x())
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
                percentage, unit, userdist = result
                if percentage * 100 != 0:
                    send = float(userdist) / float(percentage * 100)
                else:
                    send = 0 

                # Check if userdist is a non-empty integer and not 0
                if userdist.isdigit() and int(userdist) != 0:
                    self.DistanceChanged.emit(percentage)
                    self.DistanceUser.emit(float(send))
                    self.unitChanged.emit(unit)
                    
                    self.close()
                else:
                    error_dialog = QErrorMessage(self)
                    error_dialog.showMessage("Enter a valid non-empty integer greater than 0 in the distance box.")
        else:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage("Pick Two Points")

    def calculate_distance_percentage(self):
        ret, frame = self.cap.read()
        if ret:
            original_height, original_width, _ = frame.shape
            displayed_width = self.image_label.width()
            displayed_height = self.image_label.height()

            if len(self.points) == 2:
                # Calculate the distance in the resized frame
                resized_distance = np.sqrt(
                    (self.points[1][0] - self.points[0][0]) ** 2 +
                    (self.points[1][1] - self.points[0][1]) ** 2
                )

                # Calculate the percentage based on the adjusted frame size
                percentage = (resized_distance / np.sqrt(displayed_width ** 2 + displayed_height ** 2)) * 100

                unit = self.unit_combobox.currentText()
                userdist = self.distance_input.text()

                return percentage, unit, userdist

        return None
   
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PointSelectorApp(camera_index=1)
    window.show()
    sys.exit(app.exec_())
