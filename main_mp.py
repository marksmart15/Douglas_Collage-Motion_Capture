# main_mp.py
import os
import cv2
import mediapipe as mp
import time
import sys
from pose_estimator_mp import PoseEstimatorMP
from distancePicker import PointSelectorApp

from PyQt5.QtWidgets import QApplication,QFileDialog, QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QCheckBox, QLineEdit, QErrorMessage, QGroupBox, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class VideoImgManager:
    def __init__(self):
        self.POSE_ESTIMATOR = PoseEstimatorMP()
        
    def show_frame_fullscreen(self, frame):
        # Get the screen resolution
        screen_width, screen_height = 1920, 1080  # You can replace these values with the actual screen resolution

        # Get the frame dimensions
        frame_width, frame_height = frame.shape[1], frame.shape[0]

        # Calculate the scaling factors for width and height
        scale_width = screen_width / frame_width
        scale_height = screen_height / frame_height

        # Choose the minimum scaling factor to maintain the aspect ratio
        min_scale = min(scale_width, scale_height)

        # Calculate the new dimensions
        new_width = int(frame_width * min_scale)
        new_height = int(frame_height * min_scale)

        # Resize the frame to fit the screen
        resized_frame = cv2.resize(frame, (new_width, new_height))

        # Create a full-screen window
        cv2.namedWindow('Pose Landmarker', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Pose Landmarker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Show the resized frame in the full-screen window
        cv2.imshow('Pose Landmarker', resized_frame)
        
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

            self.show_frame_fullscreen(frame)

            if cv2.waitKey(1) & 0xFF == 27:  # 'Esc' key
                break

        cap.release()
        cv2.destroyAllWindows()

        # Export data to CSV file if save_data is True
        if save_data:
            pose_estimator.save_data_after_estimation()


class GUI(QWidget):
    has_not_happend = True
    percentage = -1
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.save_location = ""
        self.file_name = ""
        self.data_points_var = ""
        self.video_file_path = ""
        self.reference_frame = None
           
        self.init_ui()

    def init_ui(self):
        # Outer box (parent widget)
        outer_box = QGroupBox(self)
        outer_box.setStyleSheet("""
            QGroupBox {
                background-color: #F0F0F0;
                border: 0px solid #ddd;
                border-radius: 20px;
                margin: 10px;
            }
        """)

        # Inner box (child widget)
        inner_box = QWidget(outer_box)
        inner_box.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        # Create widgets
        self.label_device = QLabel("Or Select Video Device:")
        self.device_combobox = QComboBox()
        video_devices = self.list_video_devices()
        self.device_combobox.addItems(video_devices)

        self.label_joint = QLabel("Select Joint:")
        self.joint_combobox = QComboBox()
        self.joint_combobox.addItems(["SKELETON", "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW", "RIGHT_WRIST", "LEFT_WRIST", "RIGHT_HIP", "LEFT_HIP", "RIGHT_KNEE", "LEFT_KNEE", "RIGHT_ANKLE", "LEFT_ANKLE"])

        #self.label_axis = QLabel("Select Axis:")
        #self.axis_combobox = QComboBox()
        #self.axis_combobox.addItems(["X-axis", "Y-axis", "Both"])

        #self.remove_background_checkbox = QCheckBox("Remove Background")

        # Additional widgets (add more as needed)
        self.save_data_checkbox = QCheckBox("Save Data")
        self.label_data_points = QLabel("Data Points Per Second:")
        self.entry_data_points = QLineEdit()
        
        self.label_video_file = QLabel("Select Video File:")
        self.label_selected_file = QLabel("")
        self.button_browse_video = QPushButton("Browse .mp4, .avi and .mkv")
        self.button_browse_video.clicked.connect(self.browse_video_file)

        # Add widgets to the layout

        self.button_start = QPushButton("Start Estimation")
        self.button_start.clicked.connect(self.start_estimation)
        
        self.button_distance = QPushButton("Set Distance Reference")
        self.button_distance.clicked.connect(self.start_distance_picker)
        
        # Layout for the inner box
        inner_layout = QVBoxLayout(inner_box)
        inner_layout.addWidget(self.label_video_file)
        inner_layout.addWidget(self.button_browse_video)
        inner_layout.addWidget(self.label_selected_file)
        inner_layout.addWidget(self.label_device)
        inner_layout.addWidget(self.device_combobox)
        inner_layout.addWidget(self.label_joint)
        inner_layout.addWidget(self.joint_combobox)
        #inner_layout.addWidget(self.label_axis)
        #inner_layout.addWidget(self.axis_combobox)
        #inner_layout.addWidget(self.remove_background_checkbox)
        inner_layout.addWidget(self.save_data_checkbox)
        inner_layout.addWidget(self.label_data_points)
        inner_layout.addWidget(self.entry_data_points)
        inner_layout.addWidget(self.button_distance)
        inner_layout.addWidget(self.button_start)

        # Layout for the outer box
        outer_layout = QVBoxLayout(outer_box)
        outer_layout.addWidget(inner_box)

        # Set layout for the main widget (self)
        self.setLayout(outer_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox:hover {
                background-color: #45a049;
                font-size: 12px;
                padding: 5px;
                border: 1px solid #ccc;
            }
            QComboBox, QLineEdit {
                font-size: 12px;
                padding: 5px;
                border: 1px solid #ccc;
            }
            QCheckBox {
                font-size: 12px;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px;
                background-color: #2672DE;
                color: black;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #26ACDE;
            }
    """)

        
    def list_video_devices(self):
        devices = []
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append(f"Device {i}: {cap.get(cv2.CAP_PROP_FPS)} FPS")
            cap.release()
        return devices
    
    def start_distance_picker(self):

        video_device = int(self.device_combobox.currentText().split(":")[0].split(" ")[-1])
        self.distance_picker_dialog = PointSelectorApp(video_device)
        
        self.distance_picker_dialog.DistanceChanged.connect(self.handle_distance_changed)
        self.distance_picker_dialog.DistanceUser.connect(self.handle_distance_user)
        self.distance_picker_dialog.unitChanged.connect(self.handle_unit_changed)
        self.distance_picker_dialog.show()

    def handle_distance_changed(self, percentage):
        #print(percentage)
        self.percentage = percentage

    def handle_distance_user(self, user_distance):
        #print("entered amount ", user_distance)
        self.user_distance = user_distance

    def handle_unit_changed(self, unit):
        #print("unit ",unit)
        self.unit = unit
    
    def browse_video_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv)", options=options)
        if file_path:
            self.video_file_path = file_path
            self.label_selected_file.setText(os.path.basename(file_path))  # Display only the file name
            
    def start_estimation(self):
        if self.percentage == -1:
            self.has_not_happend = False
            self.start_distance_picker()
            self.show_error("Must Pick Refrence Distance")
        else:
            chosen_joint = self.joint_combobox.currentText()
            chosen_axis = None #self.axis_combobox.currentText().lower()
            video_device = int(self.device_combobox.currentText().split(":")[0].split(" ")[-1])
            save_data = self.save_data_checkbox.isChecked()
            data_points_input = self.entry_data_points.text()
            data_points_per_second = int(data_points_input) if data_points_input.isdigit() and 1 <= int(
                data_points_input) <= 30 else None
            percentage = self.percentage
            userDistance = self.user_distance
            unit = self.unit

            if data_points_input and data_points_per_second is None:
                self.show_error("Data points per second must be a valid digit between 1 and 30 or empty for max frames.")
                return
            else:
                file_name = ""  # No file name if not saving data
                save_location = ""
                
            if self.video_file_path:
                # Get the selected video file path
                video_type = self.video_file_path
                # Start estimation with the selected video file
                self.main_app.start_estimation(chosen_joint, chosen_axis, video_type, save_data, save_location, file_name, percentage, userDistance, unit, data_points_per_second=None)
            else:
                self.main_app.start_estimation(chosen_joint, chosen_axis, video_device, save_data, save_location, file_name,percentage,userDistance,unit, data_points_per_second)

    def show_error(self, message):
        error_dialog = QErrorMessage(self)
        error_dialog.showMessage(message)
    
class Main:
    def __init__(self):
        self.VI_M = VideoImgManager()

    def start_estimation(self, chosen_joint, chosen_axis, video_type, save_data, save_location, file_name,percentage,userDistance,unit, data_points_per_second=None):
        if not file_name:
            file_name = "output.csv"  # Default file name if not provided

        pose_estimator = PoseEstimatorMP(chosen_joint, chosen_axis, save_location, file_name,percentage,userDistance,unit,data_points_per_second)
        self.VI_M.start_video_recording(pose_estimator, video_type, save_data)


if __name__ == '__main__':
    app = QApplication([])
    main_app = Main()
    gui = GUI(main_app)
    gui.show()
    app.exec_()