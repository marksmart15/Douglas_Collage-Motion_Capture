# pose_estimator_mp.py

import cv2
import mediapipe as mp
import math
import csv
import time
import os
from utils import get_joint_combinations
from tkinter import filedialog

class PoseEstimatorMP:
    def __init__(self, chosen_joint="LEFT_SHOULDER", chosen_axis="x", save_location="", file_name="motion_data.csv", data_points_per_second=None):
        self.mp_pose = mp.solutions.pose
        self.pose_landmarker = self.mp_pose.Pose()
        self.results = None
        self.data = []
        self.start_time = None
        self.chosen_joint = chosen_joint
        self.chosen_axis = chosen_axis.lower()
        self.save_location = save_location
        self.file_name = file_name
        self.data_points_per_second = data_points_per_second
        self.last_frame_time = time.time()

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
                # Calculate angle change
                angle_change = self.calculate_angle(joint1_position, joint2_position, joint_elbow_position)

                # Draw the chosen joint and angle on the frame
                joint_x, joint_y = int(joint_elbow_position[0] * frame.shape[1]), int(joint_elbow_position[1] * frame.shape[0])
                cv2.putText(frame, f'{angle_change:.2f}',
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

            if self.start_time is None:
                self.start_time = time.time()

            timestamp = time.time() - self.start_time  # Adjust timestamp to start from 0

            # Calculate angle change
            angle_change = self.calculate_angle(joint1_position, joint2_position, joint_elbow_position)

            self.data.append([timestamp, angle_change, joint_elbow_position])

            # Draw the chosen joint and angle on the frame
            joint_x, joint_y = int(joint_elbow_position[0] * frame.shape[1]), int(joint_elbow_position[1] * frame.shape[0])
            cv2.putText(frame, f'{angle_change:.2f}',
                        (joint_x, joint_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    
    def export_data_to_csv(self):
        if self.save_location:
            base_name, ext = os.path.splitext(self.file_name)
            if not ext:
                ext = ".csv"

            file_path = os.path.join(self.save_location, self.file_name)

            # Handle filename collisions
            count = 1
            while os.path.exists(file_path):
                file_path = os.path.join(self.save_location, f"{base_name}_{count}{ext}")
                count += 1
        else:
            self.save_location = filedialog.askdirectory()
            file_path = os.path.join(self.save_location, self.file_name)

            # Handle filename collisions
            base_name, ext = os.path.splitext(self.file_name)
            if not ext:
                ext = ".csv"

            count = 1
            while os.path.exists(file_path):
                file_path = os.path.join(self.save_location, f"{base_name}_{count}{ext}")
                count += 1

        with open(file_path, mode='w', newline='') as csv_file:
            fieldnames = ['Timestamp', 'Angle Change', 'Joint Position']
            writer = csv.writer(csv_file)
            writer.writerow(fieldnames)

            for row in self.data:
                # Round Timestamp to the nearest hundredth, others to the nearest tenth
                rounded_row = [round(value, 2) if index == 0 else round(value, 1) if isinstance(value, (float, int)) else value for index, value in enumerate(row)]
                writer.writerow(rounded_row)