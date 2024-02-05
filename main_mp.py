# main_mp.py
import os
from utils import get_joint_combinations
import cv2
import mediapipe as mp
from pose_estimator_mp import PoseEstimatorMP
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QComboBox, \
    QPushButton, QCheckBox, QLineEdit, QErrorMessage
from PyQt5.QtCore import Qt

class VideoImgManager():
    def __init__(self):
        self.POSE_ESTIMATOR = PoseEstimatorMP()

    def start_video_recording(self, pose_estimator, videoType, save_data, data_points_per_second=None):
        cap = cv2.VideoCapture(videoType)

        if data_points_per_second:
            pose_estimator.data_points_per_second = data_points_per_second
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_estimator.pose_landmarker.process(rgb_frame)
            pose_estimator.results = results

            if data_points_per_second:
                current_time = time.time()
                elapsed_time = current_time - last_time

                if elapsed_time < time_interval:
                    continue  # Skip processing this frame

                last_time = current_time

            # Pass chosen_joint to process_landmarks
            pose_estimator.process_landmarks(frame, pose_estimator.chosen_joint)

            # Draw the landmarks on the frame
            mp.solutions.drawing_utils.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)

            cv2.imshow('Pose Landmarker', frame)

            if cv2.waitKey(1) & 0xFF == 27:  # 'Esc' key
                break

        cap.release()
        cv2.destroyAllWindows()

        # Export data to CSV file if save_data is True
        if save_data:
            pose_estimator.export_data_to_csv()


class GUI(QWidget):
    def __init__(self, main_app):
        super().__init__()

        self.main_app = main_app
        self.save_location = ""
        self.file_name = ""
        self.data_points_var = ""

        self.init_ui()

    def init_ui(self):
        # Create widgets
        self.label_device = QLabel("Select Video Device:")
        self.device_combobox = QComboBox()
        video_devices = self.list_video_devices()
        self.device_combobox.addItems(video_devices)

        self.label_joint = QLabel("Select Joint:")
        self.joint_combobox = QComboBox()
        self.joint_combobox.addItems(["LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW", "RIGHT_WRIST", "LEFT_WRIST", "RIGHT_HIP", "LEFT_HIP", "RIGHT_KNEE", "LEFT_KNEE", "RIGHT_ANKLE", "LEFT_ANKLE"])

        self.label_axis = QLabel("Select Axis:")
        self.axis_combobox = QComboBox()
        self.axis_combobox.addItems(["X-axis", "Y-axis"])

        self.remove_background_checkbox = QCheckBox("Remove Background")

        self.save_data_checkbox = QCheckBox("Save Data")
        self.label_filename = QLabel("Enter File Name:")
        self.entry_filename = QLineEdit()
        self.label_data_points = QLabel("Data Points Per Second:")
        self.entry_data_points = QLineEdit()

        self.button_start = QPushButton("Start Estimation")
        self.button_start.clicked.connect(self.start_estimation)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_device)
        layout.addWidget(self.device_combobox)
        layout.addWidget(self.label_joint)
        layout.addWidget(self.joint_combobox)
        layout.addWidget(self.label_axis)
        layout.addWidget(self.axis_combobox)
        layout.addWidget(self.remove_background_checkbox)
        layout.addWidget(self.save_data_checkbox)
        layout.addWidget(self.label_filename)
        layout.addWidget(self.entry_filename)
        layout.addWidget(self.label_data_points)
        layout.addWidget(self.entry_data_points)
        layout.addWidget(self.button_start)

        self.setLayout(layout)

    def list_video_devices(self):
        devices = []
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append(f"Device {i}: {cap.get(cv2.CAP_PROP_FPS)} FPS")
            cap.release()
        return devices

    def start_estimation(self):
        chosen_joint = self.joint_combobox.currentText()
        chosen_axis = self.axis_combobox.currentText().lower()
        video_device = int(self.device_combobox.currentText().split(":")[0].split(" ")[-1])
        save_data = self.save_data_checkbox.isChecked()
        file_name = self.entry_filename.text() or "output"
        data_points_input = self.entry_data_points.text()
        data_points_per_second = int(data_points_input) if data_points_input.isdigit() and 1 <= int(
            data_points_input) <= 30 else None

        if data_points_input and data_points_per_second is None:
            self.show_error("Data points per second must be a valid digit between 1 and 30.")
            return

        if not all(c not in r'\/:*?"<>|' for c in file_name):
            self.show_error("File name contains invalid characters.")
            return

        if not file_name.endswith(".csv"):
            file_name += ".csv"

        self.main_app.live_estimation(chosen_joint, chosen_axis, video_device, save_data,
                                      self.save_location, file_name, data_points_per_second)

    def show_error(self, message):
        error_dialog = QErrorMessage(self)
        error_dialog.showMessage(message)


class Main:
    def __init__(self):
        self.VI_M = VideoImgManager()

    def live_estimation(self, chosen_joint, chosen_axis, video_type, save_data, save_location, file_name,
                        data_points_per_second=None):
        pose_estimator = PoseEstimatorMP(chosen_joint, chosen_axis, save_location, file_name,
                                         data_points_per_second)
        self.VI_M.start_video_recording(pose_estimator, video_type, save_data)


if __name__ == '__main__':
    app = QApplication([])
    main_app = Main()
    gui = GUI(main_app)
    gui.show()
    app.exec_()
    
    
