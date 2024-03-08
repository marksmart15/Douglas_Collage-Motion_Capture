# pose_estimator_mp.py
import cv2
import mediapipe as mp
import math
import csv
import time
import os
import psutil
from utils import get_joint_combinations
from tkinter import filedialog
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class PointTracker:
    def __init__(self, screen_diagonal_percentage, distance_that_persentage_represents):
        self.screen_diagonal_percentage = screen_diagonal_percentage
        self.meter_stick_length_cm = distance_that_persentage_represents
        self.meter_stick_length_pixels = (screen_diagonal_percentage / 100) * self.meter_stick_length_cm
        self.initial_point_x = None
        self.initial_point_y = None

    def set_initial_point(self, initial_percentage):
        if self.initial_point_x is None:
            # Use the x-value of joint_position to set the initial point
            self.initial_point_x = initial_percentage[0]# / 100) * self.meter_stick_length_pixels
            self.initial_point_y = initial_percentage[1]# / 100) * self.meter_stick_length_pixels
            
        else:
            raise ValueError("Initial point already set.")

class PoseEstimatorMP:
    def __init__(self, chosen_joint="LEFT_SHOULDER", chosen_axis="x", save_location="", file_name="motion_data.csv", distance_percentage=0, user_distance=100, unit=0, data_points_per_second=None):
        self.mp_pose = mp.solutions.pose
        self.pose_landmarker = self.mp_pose.Pose()
        self.results = None
        self.data = []
        self.start_time = None
        self.chosen_joint = chosen_joint
        self.chosen_axis = None#chosen_axis.lower()
        self.save_location = save_location
        self.file_name = file_name
        self.data_points_per_second = data_points_per_second
        self.last_frame_time = time.time()
        self.userDistance = user_distance
        self.unit = unit
        self.tracker = PointTracker(distance_percentage, user_distance)  # Change the percentage accordingly

    def calculate_angle(self, joint1, joint2, joint_common):
        vector1 = (joint1[0] - joint_common[0], joint1[1] - joint_common[1])
        vector2 = (joint2[0] - joint_common[0], joint2[1] - joint_common[1])

        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
        magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

        cos_theta = dot_product / (magnitude1 * magnitude2)
        angle_rad = math.acos(cos_theta)

        angle_deg = math.degrees(angle_rad)
        return angle_deg

    def calculate_adjusted_distance(self, user_distance, joint_position):
        # Calculate the adjusted distance based on the percentage and user-provided distance
        adjusted_distance_x = (user_distance * ((joint_position[0] - self.tracker.initial_point_x)*100))*100
        adjusted_distance_y = (user_distance * ((joint_position[1] - self.tracker.initial_point_y)*100))*100

        return adjusted_distance_x, adjusted_distance_y
    
    def calculate_angle_and_displacement(self, joint1_position, joint2_position, joint_elbow_position):
        if self.tracker.initial_point_x is None:
            raise ValueError("Initial point not set. Call set_initial_point first.")

        # Calculate angle
        angle = self.calculate_angle(joint1_position, joint2_position, joint_elbow_position)

        # Calculate adjusted distance
        adjusted_distance_x, adjusted_distance_y = self.calculate_adjusted_distance(
            self.userDistance, joint_elbow_position)

        return angle, adjusted_distance_x, adjusted_distance_y

    def process_landmarks(self, frame, chosen_joint):
        current_time = time.time()
        elapsed_time = current_time - self.last_frame_time
        if self.data_points_per_second and elapsed_time < 1 / self.data_points_per_second:

            if self.results.pose_landmarks:
                joint1, joint2, joint_elbow = get_joint_combinations(chosen_joint)
                
                joint1_position = (
                    self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint1].value].x,
                    self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint1].value].y
                )

                joint2_position = (
                    self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint2].value].x,
                    self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint2].value].y
                )

                joint_elbow_position = (
                    self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint_elbow].value].x,
                    self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint_elbow].value].y
                )
                #print("joint center = %", int(joint_elbow_position[0] * 100),", ", int(joint_elbow_position[1] * 100) )
                if self.start_time is None:
                    self.start_time = time.time()

                    # Set the initial point for the first frame
                    self.tracker.set_initial_point(joint_elbow_position)

                timestamp = time.time() - self.start_time  # Adjust timestamp to start from 0

                # Calculate angle and displacement
                angle, adjusted_distance_x, adjusted_distance_y = self.calculate_angle_and_displacement(joint1_position, joint2_position, joint_elbow_position)

                # Include angle and adjusted distance in the CSV output
                if self.data_points_per_second == None:
                    self.data.append([timestamp, adjusted_distance_x, adjusted_distance_y, angle,])

                # Draw the chosen joint and adjusted distance on the frame
                joint_x, joint_y = int(joint_elbow_position[0] * frame.shape[1]), int(joint_elbow_position[1] * frame.shape[0])
                cv2.putText(frame, f'Angle: {angle:.2f}',
                        (joint_x, joint_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            return  # Skip processing this frame

        self.last_frame_time = current_time



        if self.results.pose_landmarks:
            joint1, joint2, joint_elbow = get_joint_combinations(chosen_joint)
            
            joint1_position = (
                self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint1].value].x,
                self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint1].value].y
            )

            joint2_position = (
                self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint2].value].x,
                self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint2].value].y
            )

            joint_elbow_position = (
                self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint_elbow].value].x,
                self.results.pose_landmarks.landmark[self.mp_pose.PoseLandmark[joint_elbow].value].y
            )
            #print("joint center = %", int(joint_elbow_position[0] * 100),", ", int(joint_elbow_position[1] * 100) )
            if self.start_time is None:
                self.start_time = time.time()

                # Set the initial point for the first frame
                self.tracker.set_initial_point(joint_elbow_position)

            timestamp = time.time() - self.start_time  # Adjust timestamp to start from 0

            # Calculate angle and displacement
            angle, adjusted_distance_x, adjusted_distance_y = self.calculate_angle_and_displacement(joint1_position, joint2_position, joint_elbow_position)

            # Include angle and adjusted distance in the CSV output

            self.data.append([timestamp, adjusted_distance_x, adjusted_distance_y, angle,])

            # Draw the chosen joint and adjusted distance on the frame
            joint_x, joint_y = int(joint_elbow_position[0] * frame.shape[1]), int(joint_elbow_position[1] * frame.shape[0])
            cv2.putText(frame, f'Angle: {angle:.2f}',
                        (joint_x, joint_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        
    def is_file_open(self, file_path):
        try:
            file_descriptor = os.open(file_path, os.O_RDWR)
            process_info = psutil.Process(psutil.Process().pid).open_files()[file_descriptor]
            os.close(file_descriptor)

            if process_info:
                print(f"The file is open by process {process_info.pid}.")
                return True
            else:
                print("The file is not open.")
                return False
        except PermissionError as e:
            print(f"Permission denied: {e}")
            self.show_error_message("Permission Denied", "Window already open close and try again.")
            return True  # Permission denied, return True
        except Exception as e:
            print(f"Error checking file status: {e}")
            return False

    def show_error_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def save_data_after_estimation(self):
        if self.save_location:
            default_file_name = os.path.join(self.save_location, "default_name.csv")
        else:
            default_file_name = "Output.csv"

        file_path = filedialog.asksaveasfilename(
            initialdir=self.save_location,
            title="Save Motion Data",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            defaultextension=".csv",
            initialfile=default_file_name
        )

        if file_path:
            if not self.is_file_open(file_path):  # Check if the file is open
                with open(file_path, mode='w', newline='') as csv_file:
                    fieldnames = ['Timestamp', 'Adjusted Distance X', 'Adjusted Distance Y', 'Angle']
                    writer = csv.writer(csv_file)
                    writer.writerow(fieldnames)

                    for row in self.data:
                        timestamp, adjusted_distance_x, adjusted_distance_y, joint_position = row
                        rounded_row = [round(value, 2) if isinstance(value, (float, int)) else value for value in [timestamp, adjusted_distance_x, adjusted_distance_y, joint_position]]
                        writer.writerow(rounded_row)
            else:
                self.save_data_after_estimation()
