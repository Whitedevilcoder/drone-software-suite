import os
import torch

# --- FLIGHT SETTINGS ---
CRUISE_ALTITUDE = -18.0
PATROL_SPEED = 2.5
OBSTACLE_TRIGGER_DIST = 5.0
CMD_INTERVAL = 0.1  # Send movement commands at 10 Hz to prevent API flooding

WAYPOINTS = [
    (30.0, 0.0, CRUISE_ALTITUDE),
    (30.0, 25.0, CRUISE_ALTITUDE),
    (0.0, 25.0, CRUISE_ALTITUDE),
    (0.0, 0.0, CRUISE_ALTITUDE)
]

# --- AI & VISION SETTINGS ---
USE_DEVICE = 0 if torch.cuda.is_available() else "cpu"
MODEL_PATH = "yolov8n.engine"
CONFIDENCE_THRESHOLD = 0.45

# Essential targets only (Ignore people, stop signs, etc.)
# YOLOv8 Classes: 2=Car, 3=Motorcycle, 5=Bus, 7=Truck
TARGET_CLASSES = [2, 3, 5, 7] 

# --- LOGGING SETTINGS ---
OUTPUT_DIR = "alerts"
CSV_FILE = os.path.join(OUTPUT_DIR, "mission_log.csv")