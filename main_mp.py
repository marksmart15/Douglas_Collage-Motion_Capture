# main_mp.py
from tkinter import messagebox
from tkinter import ttk
import os
from utils import get_joint_combinations
import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import Button, Label, Entry, Checkbutton, OptionMenu, StringVar, filedialog, Frame
from pose_estimator_mp import PoseEstimatorMP

class Main:
    def __init__(self):
        self.VI_M = VideoImgManager()

    def img_estimation(self, img_path):
        self.VI_M.estimate_img(img_path)

    def live_estimation(self, chosen_joint, chosen_axis, videoType, save_data, save_location, file_name, data_points_per_second=None):
        pose_estimator = PoseEstimatorMP(chosen_joint, chosen_axis, save_location, file_name, data_points_per_second)
        self.VI_M.start_video_recording(pose_estimator, videoType, save_data)

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
            
class GUI(tk.Tk):
    def __init__(self, main_app):
        super().__init__()
        self.title("Douglas Motion Capture")
        self.geometry("400x600")
        self.minsize(400, 400)  # Lock the minimum size of the window
        self.maxsize(400, 400)  # Lock the maximum size of the window
        self.configure(bg="grey")

        self.main_app = main_app
        self.save_location = ""
        self.file_name = ""
        self.data_points_var = tk.StringVar()  # Variable to store the user input

        main_frame = Frame(self, bg="grey")
        main_frame.pack(fill="both", expand=True)

        # Dropdown menu for video device selection
        self.label_device = Label(main_frame, text="Select Video Device:", font=("Arial", 14), bg="grey")
        self.label_device.grid(row=0, column=0, pady=5)
        self.device_var = StringVar(self)
        video_devices = self.list_video_devices()
        self.device_var.set(video_devices[0] if video_devices else "No video devices")
        self.device_dropdown = OptionMenu(main_frame, self.device_var, *video_devices)
        self.device_dropdown.grid(row=0, column=1, pady=5)

        # Dropdown menu for joint selection
        self.label_joint = Label(main_frame, text="Select Joint:", font=("Arial", 14), bg="grey")
        self.label_joint.grid(row=1, column=0, pady=5)
        self.joint_var = StringVar(self)
        self.joint_var.set("LEFT_SHOULDER")  # Default joint
        self.joint_options = ["LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW"]  # Add more joints as needed
        self.joint_dropdown = OptionMenu(main_frame, self.joint_var, *self.joint_options)
        self.joint_dropdown.grid(row=1, column=1, pady=5)

        # Dropdown menu for axis selection
        self.label_axis = Label(main_frame, text="Select Axis:", font=("Arial", 14), bg="grey")
        self.label_axis.grid(row=2, column=0, pady=5)
        self.axis_var = StringVar(self)
        self.axis_var.set("X-axis")  # Default axis
        self.axis_options = ["X-axis", "Y-axis"]  # Add more options if needed
        self.axis_dropdown = OptionMenu(main_frame, self.axis_var, *self.axis_options)
        self.axis_dropdown.grid(row=2, column=1, pady=5)
        
        # Checkbox for removing background 
        self.remove_background_var = tk.IntVar()
        self.remove_background_checkbox = Checkbutton(main_frame, text="Remove Background", variable=self.remove_background_var, font=("Arial", 12), bg="grey")
        self.remove_background_checkbox.grid(row=3, column=0, pady=5, columnspan=3, sticky="w")

        # Checkbox for data saving
        self.save_data_var = tk.IntVar()
        self.save_data_checkbox = Checkbutton(main_frame, text="Save Data", variable=self.save_data_var, font=("Arial", 12), bg="grey", command=self.toggle_save_options)
        self.save_data_checkbox.grid(row=4, column=0, pady=5, columnspan=3, sticky="w")

        # Entry for file name (initially hidden)
        self.label_filename = Label(main_frame, text="Enter File Name:", font=("Arial", 14), bg="grey")
        self.entry_filename = Entry(main_frame, font=("Arial", 12))
        self.label_filename.grid(row=5, column=0, pady=5, sticky="w")
        self.entry_filename.grid(row=5, column=1, pady=5, columnspan=2, sticky="ew")
        self.label_filename.grid_remove()
        self.entry_filename.grid_remove()

        # Entry for data points per second (initially hidden)
        self.label_data_points = Label(main_frame, text="Data Points Per Second:", font=("Arial", 14), bg="grey")
        self.entry_data_points = Entry(main_frame, textvariable=self.data_points_var, font=("Arial", 12))
        self.label_data_points.grid(row=6, column=0, pady=5, sticky="w")
        self.entry_data_points.grid(row=6, column=1, pady=5, columnspan=2, sticky="ew")
        self.label_data_points.grid_remove()
        self.entry_data_points.grid_remove()

        start_button_text = "Start Estimation"
        self.button_start = Button(main_frame, text=start_button_text, command=self.start_estimation, font=("Arial", 12),
                                   width=len(start_button_text))
        self.button_start.grid(row=7, column=1, pady=10, columnspan=1, sticky="nsew")

        # Disable resizing of the window
        self.resizable(False, False)

    def toggle_save_options(self):
        # Toggle the visibility of the save options based on the save_data checkbox
        if self.save_data_var.get():
            self.label_filename.grid()
            self.entry_filename.grid()
            self.label_data_points.grid()
            self.entry_data_points.grid()
        else:
            self.label_filename.grid_remove()
            self.entry_filename.grid_remove()
            self.label_data_points.grid_remove()
            self.entry_data_points.grid_remove()
        
    
    def list_video_devices(self):
        devices = []
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append((f"Device {i}: {cap.get(cv2.CAP_PROP_FPS)} FPS", i))
            cap.release()
        return devices


    def start_estimation(self):
        # Get user inputs
        chosen_joint = self.joint_var.get()
        chosen_axis = self.axis_var.get().lower()
        video_device = int(self.device_var.get().split(":")[0].split(" ")[-1])
        save_data = self.save_data_var.get() == 1
        file_name = self.entry_filename.get() or "output"
        
        # Validate data points per second if it's not empty
        data_points_input = self.data_points_var.get()
        data_points_per_second = int(data_points_input) if data_points_input.isdigit() and 1 <= int(data_points_input) <= 30 else None
        if data_points_input and data_points_per_second is None:
            messagebox.showerror("Error", "Data points per second must be a valid digit between 1 and 30.")
            return  # Exit the function if validation fails

        # Validate file name for Windows compatibility
        if not all(c not in r'\/:*?"<>|' for c in file_name):
            messagebox.showerror("Error", "File name contains invalid characters.")
            return  # Exit the function if validation fails

        # Ensure the file name has the .csv extension
        if not file_name.endswith(".csv"):
            file_name += ".csv"

        # Continue with the estimation
        self.main_app.live_estimation(chosen_joint, chosen_axis, video_device, save_data, self.save_location, file_name, data_points_per_second)

if __name__ == "__main__":
    app = Main()
    gui = GUI(app)
    gui.mainloop()
