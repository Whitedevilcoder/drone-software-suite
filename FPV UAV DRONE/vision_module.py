import cv2
import numpy as np
import os
import csv
import time
from datetime import datetime
from ultralytics import YOLO
from config import *

class ReconVision:
    def __init__(self):
        print(f"[TACTICAL AI] Booting Inference Core on Device: {USE_DEVICE}")
        self.model = YOLO(MODEL_PATH)
        self.active_target_id = -1
        self.target_log_timers = {} 
        
        # --- NEW: GEO-SPATIAL MEMORY BANK ---
        self.spatial_memory = [] 
        self.SPATIAL_TOLERANCE = 8.0 # Meters radius to classify a vehicle as "already logged"
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode="w", newline="") as f:
                writer = csv.writer(f)
                # Added 'Status' column to track New vs Re-detected targets
                writer.writerow(["Timestamp", "Class", "Confidence", "Pos_X", "Pos_Y", "Altitude_M", "Speed_MS", "Snapshot_File", "Status"])

    def decode_frame(self, image_response):
        encoded_data = np.frombuffer(image_response.image_data_uint8, dtype=np.uint8)
        return cv2.imdecode(encoded_data, cv2.IMREAD_COLOR)

    def process_depth(self, depth_response):
        dh, dw = depth_response.height, depth_response.width
        depth_raw = np.array(depth_response.image_data_float, dtype=np.float32).reshape(dh, dw)
        
        depth_clean = np.where((depth_raw > 1.5) & (depth_raw < 60.0), depth_raw, 60.0)
        
        y_start, y_end = int(dh * 0.4), int(dh * 0.6)
        x_third = dw // 3
        
        left_sector = depth_clean[y_start:y_end, 0:x_third]
        center_sector = depth_clean[y_start:y_end, x_third:2 * x_third]
        right_sector = depth_clean[y_start:y_end, 2 * x_third:dw]

        dist_left = float(np.min(left_sector))
        dist_center = float(np.min(center_sector))
        dist_right = float(np.min(right_sector))

        depth_clipped = np.clip(depth_raw, 2.0, 45.0)
        thermal_norm = (255 * (depth_clipped - 2.0) / 43.0).astype(np.uint8)
        thermal_colored = cv2.applyColorMap(255 - thermal_norm, cv2.COLORMAP_INFERNO)
        
        return dist_left, dist_center, dist_right, thermal_colored

    def detect_and_track(self, frame_rgb, pos, alt, speed_ms):
        results = self.model.track(
            source=frame_rgb, persist=True, tracker="botsort.yaml",
            conf=CONFIDENCE_THRESHOLD, classes=TARGET_CLASSES, 
            verbose=False, device=USE_DEVICE
        )
        
        annotated_rgb = results[0].plot()
        boxes = results[0].boxes
        target_cx, target_cy, error_x = None, None, None
        active_class = "NONE"
        
        if len(boxes) > 0:
            confs = boxes.conf.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)
            curr_time = time.time()
            
            if boxes.id is not None:
                ids = boxes.id.cpu().numpy().astype(int)
            else:
                ids = np.arange(len(boxes)) * -1 - 1
                
            # 1. SPATIAL SURVEILLANCE PIPELINE
            for i in range(len(boxes)):
                box_id = ids[i]
                conf = confs[i]
                label = self.model.names[clss[i]].upper()
                
                if conf >= CONFIDENCE_THRESHOLD and (curr_time - self.target_log_timers.get(box_id, 0)) > 2.0:
                    
                    # Cross-reference current telemetry against spatial memory
                    is_known_stationary = False
                    for memory in self.spatial_memory:
                        dist = np.sqrt((pos.x_val - memory['x'])**2 + (pos.y_val - memory['y'])**2)
                        if dist < self.SPATIAL_TOLERANCE and memory['class'] == label:
                            is_known_stationary = True
                            break
                            
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
                    id_tag = f"ID{box_id}" if box_id >= 0 else f"UNTRACKED_{i}"
                    
                    if not is_known_stationary:
                        # NEW TARGET: Process crop, save to disk, and log to memory bank
                        img_filename = f"{label}_{id_tag}_{ts}.jpg"
                        b = boxes[i]
                        x1, y1, x2, y2 = map(int, b.xyxy[0])
                        crop = frame_rgb[max(0, y1):min(frame_rgb.shape[0], y2), max(0, x1):min(frame_rgb.shape[1], x2)]
                        
                        if crop.size > 0:
                            cv2.imwrite(os.path.join(OUTPUT_DIR, img_filename), crop)
                            with open(CSV_FILE, mode="a", newline="") as f:
                                csv.writer(f).writerow([ts, f"{label}-{id_tag}", f"{conf:.2f}", f"{pos.x_val:.2f}", f"{pos.y_val:.2f}", f"{alt:.2f}", f"{speed_ms:.2f}", img_filename, "NEW_TARGET"])
                            
                            self.spatial_memory.append({'class': label, 'x': pos.x_val, 'y': pos.y_val})
                    else:
                        # KNOWN TARGET: Bypass image processing, push lightweight text update
                        with open(CSV_FILE, mode="a", newline="") as f:
                            csv.writer(f).writerow([ts, f"{label}-{id_tag}", f"{conf:.2f}", f"{pos.x_val:.2f}", f"{pos.y_val:.2f}", f"{alt:.2f}", f"{speed_ms:.2f}", "NO_IMAGE_SAVED", "STATIONARY_UPDATE"])
                    
                    self.target_log_timers[box_id] = curr_time

            # 2. FLIGHT KINEMATICS PIPELINE
            valid_ids_mask = ids >= 0
            if np.any(valid_ids_mask):
                valid_ids = ids[valid_ids_mask]
                valid_confs = confs[valid_ids_mask]
                
                if self.active_target_id not in valid_ids:
                    best_idx = np.argmax(valid_confs)
                    self.active_target_id = valid_ids[best_idx]
                    print(f"\n[TACTICAL AI] Target Acquired - Lock ID: {self.active_target_id}")

                target_idx = np.where(ids == self.active_target_id)[0]
                if len(target_idx) > 0:
                    locked_box = boxes[target_idx[0]]
                    x1, y1, x2, y2 = map(int, locked_box.xyxy[0])
                    target_cx, target_cy = (x1 + x2) // 2, (y1 + y2) // 2
                    error_x = target_cx - (frame_rgb.shape[1] // 2)
                    active_class = self.model.names[int(locked_box.cls[0])].upper()

        return annotated_rgb, target_cx, target_cy, error_x, active_class