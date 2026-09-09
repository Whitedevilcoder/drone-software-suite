import airsim
import cv2
import numpy as np
import time
import os
import csv
import torch
from datetime import datetime
from ultralytics import YOLO

# 1. Directory & Logging Setup
output_dir = "alerts"
os.makedirs(output_dir, exist_ok=True)
csv_file = os.path.join(output_dir, "mission_log.csv")

if not os.path.exists(csv_file):
    with open(csv_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Class", "Confidence", "Pos_X", "Pos_Y", "Altitude_M", "Snapshot_File"])

# 2. AI Core
use_device = 0 if torch.cuda.is_available() else "cpu"
print(f"[TACTICAL AI] Inference Core: {use_device}")
model = YOLO("yolov8n.engine")
TARGET_CLASSES = [0, 1, 2, 3, 5, 7, 14, 15, 16, 17, 18, 19, 21]

# 3. AirSim Client Initialization
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

cv2.namedWindow("Autonomous Surveillance & Avoidance Station", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Autonomous Surveillance & Avoidance Station", 1280, 520)

print("[TACTICAL RECON] Arming and initiating launch...")
client.takeoffAsync().join()

# Clear ground, trees, and street obstacles safely at 12m
CRUISE_ALTITUDE = -25.0
PATROL_SPEED = 2.5

print(f"[TACTICAL RECON] Climbing to cruise altitude ({-CRUISE_ALTITUDE:.0f}m)...")
client.moveToZAsync(CRUISE_ALTITUDE, 2).join()
time.sleep(1)  # Stabilize altitude before initiating navigation

# Waypoints
waypoints = [
    (30.0, 0.0, CRUISE_ALTITUDE),
    (30.0, 25.0, CRUISE_ALTITUDE),
    (0.0, 25.0, CRUISE_ALTITUDE),
    (0.0, 0.0, CRUISE_ALTITUDE)
]

current_wp_idx = 0
last_log_time = 0
log_cooldown = 1.5
target_lost_time = time.time()
active_mode = "PATROL"

def navigate_to_wp(idx):
    tx, ty, tz = waypoints[idx]
    print(f"[NAV CORE] Advancing to Sector {idx + 1}/{len(waypoints)}: ({tx:.0f}, {ty:.0f})")
    return client.moveToPositionAsync(
        tx, ty, tz, PATROL_SPEED,
        drivetrain=airsim.DrivetrainType.ForwardOnly,
        yaw_mode=airsim.YawMode(False, 0)
    )

navigate_to_wp(current_wp_idx)

# Obstacle avoidance threshold
OBSTACLE_TRIGGER_DIST = 5.0

while True:
    # 1. Telemetry
    state = client.getMultirotorState()
    pos = state.kinematics_estimated.position
    alt = -pos.z_val

    # 2. Sensor Retrieval
    responses = client.simGetImages([
        airsim.ImageRequest("front_center", airsim.ImageType.Scene, False, False),
        airsim.ImageRequest("front_center", airsim.ImageType.DepthPerspective, True, False)
    ])

    if len(responses) >= 2 and responses[0].width > 0 and responses[1].width > 0:
        # RGB Processing
        raw_rgb = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
        frame_rgb = raw_rgb.reshape(responses[0].height, responses[0].width, 3).copy()
        h, w, _ = frame_rgb.shape

        # Depth Processing (use depth frame's own dimensions to prevent indexing errors)
        dh, dw = responses[1].height, responses[1].width
        depth_raw = np.array(responses[1].image_data_float, dtype=np.float32).reshape(dh, dw)

        # 3-Zone Depth Scanning (Central vertical band of the depth map)
        y_start, y_end = int(dh * 0.2), int(dh * 0.8)
        x_third = dw // 3

        left_sector = depth_raw[y_start:y_end, 0:x_third]
        center_sector = depth_raw[y_start:y_end, x_third:2 * x_third]
        right_sector = depth_raw[y_start:y_end, 2 * x_third:dw]

        # Safe distance reduction with fallback defaults
        dist_left = float(np.nanmin(left_sector)) if left_sector.size > 0 else 50.0
        dist_center = float(np.nanmin(center_sector)) if center_sector.size > 0 else 50.0
        dist_right = float(np.nanmin(right_sector)) if right_sector.size > 0 else 50.0

        # FLIR Thermal Rendering
        depth_clipped = np.clip(depth_raw, 2.0, 45.0)
        thermal_norm = (255 * (depth_clipped - 2.0) / 43.0).astype(np.uint8)
        thermal_colored = cv2.applyColorMap(255 - thermal_norm, cv2.COLORMAP_INFERNO)
        thermal_resized = cv2.resize(thermal_colored, (w, h))

        # Collision Avoidance Trigger
        if dist_center < OBSTACLE_TRIGGER_DIST or dist_left < 3.0 or dist_right < 3.0:
            active_mode = "EVADING"
            yaw_rad = airsim.to_eularian_angles(state.kinematics_estimated.orientation)[2]
            
            # Dodge toward the clearer side
            vy_body = 2.0 if dist_left < dist_right else -2.0
            vx_world = float(-0.5 * np.cos(yaw_rad) - vy_body * np.sin(yaw_rad))
            vy_world = float(-0.5 * np.sin(yaw_rad) + vy_body * np.cos(yaw_rad))

            # Sidestep and climb
            client.moveByVelocityAsync(vx_world, vy_world, -1.5, 0.3)
            annotated_rgb = frame_rgb.copy()

        else:
            # AI Inference & Tracking
            results = model.track(
                source=frame_rgb,
                persist=True,
                tracker="botsort.yaml",
                conf=0.35,
                classes=TARGET_CLASSES,
                verbose=False,
                device=use_device
            )
            annotated_rgb = results[0].plot()
            boxes = results[0].boxes
            target_count = len(boxes)

            if target_count > 0:
                active_mode = "TARGET_LOCK"
                target_lost_time = time.time()

                best_box = max(boxes, key=lambda b: float(b.conf[0]))
                x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                target_cx = (x1 + x2) // 2
                target_cy = (y1 + y2) // 2

                # Yaw tracking controller
                error_x = target_cx - (w // 2)
                yaw_rate = float(np.clip(0.08 * (error_x / (w // 2)) * 30.0, -25.0, 25.0))

                yaw_rad = airsim.to_eularian_angles(state.kinematics_estimated.orientation)[2]
                vx = float(1.5 * np.cos(yaw_rad))
                vy = float(1.5 * np.sin(yaw_rad))
                client.moveByVelocityAsync(vx, vy, 0, 0.25, airsim.DrivetrainType.MaxDegreeOfFreedom, airsim.YawMode(True, yaw_rate))

                # Reticles
                cv2.drawMarker(annotated_rgb, (target_cx, target_cy), (0, 0, 255),
                               markerType=cv2.MARKER_TILTED_CROSS, markerSize=25, thickness=2)
                cv2.drawMarker(thermal_resized, (target_cx, target_cy), (0, 255, 255),
                               markerType=cv2.MARKER_TILTED_CROSS, markerSize=25, thickness=2)

                # Snapshot capture
                conf = float(best_box.conf[0])
                if conf >= 0.45 and (time.time() - last_log_time) > log_cooldown:
                    label = model.names[int(best_box.cls[0])]
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
                    crop_img = frame_rgb[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                    if crop_img.size > 0:
                        img_filename = f"{label}_{timestamp_str}.jpg"
                        cv2.imwrite(os.path.join(output_dir, img_filename), crop_img)
                        with open(csv_file, mode="a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp_str, label, f"{conf:.2f}", f"{pos.x_val:.2f}", f"{pos.y_val:.2f}", f"{alt:.2f}", img_filename])
                        print(f"[RECON INTEL] LOGGED: {label.upper()} ({conf:.2f})")
                        last_log_time = time.time()

            else:
                # Calculate distance to current waypoint
                tx, ty, _ = waypoints[current_wp_idx]
                dist_to_wp = np.sqrt((pos.x_val - tx)**2 + (pos.y_val - ty)**2)

                # State Machine: Return to Patrol from Evasion or Target Loss
                if active_mode != "PATROL":
                    if active_mode == "TARGET_LOCK" and (time.time() - target_lost_time) <= 3.0:
                        pass # Coasting: Wait 3 seconds before giving up the search
                    else:
                        print(f"[NAV CORE] Path clear / Target lost. Resuming trajectory to Sector {current_wp_idx + 1}.")
                        active_mode = "PATROL"
                        navigate_to_wp(current_wp_idx) # Re-issue the movement command!

                # State Machine: Normal Patrol Waypoint Progression
                if active_mode == "PATROL":
                    if dist_to_wp < 2.5:
                        current_wp_idx = (current_wp_idx + 1) % len(waypoints)
                        navigate_to_wp(current_wp_idx)

       # --- Metrics Calculation ---
        # Calculate speed (m/s)
        vx = state.kinematics_estimated.linear_velocity.x_val
        vy = state.kinematics_estimated.linear_velocity.y_val
        speed_ms = np.sqrt(vx**2 + vy**2)
        
        # Calculate distance to waypoint (m)
        tx, ty, _ = waypoints[current_wp_idx]
        dist_to_wp = np.sqrt((pos.x_val - tx)**2 + (pos.y_val - ty)**2)

        # Calculate FPS
        current_time = time.time()
        fps = 1.0 / (current_time - getattr(sys.modules[__name__], 'last_frame_time', current_time - 0.03))
        last_frame_time = current_time

        # --- Telemetry Overlays ---
        mode_color = (0, 0, 255) if active_mode in ["TARGET_LOCK", "EVADING"] else (0, 255, 0)
        
        # Primary HUD (Left)
        cv2.putText(annotated_rgb, f"STATUS: {active_mode}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        cv2.putText(annotated_rgb, f"ALT: {alt:.1f}m | SPD: {speed_ms:.1f} m/s | FPS: {fps:.1f}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(annotated_rgb, f"WP DIST: {dist_to_wp:.1f}m | TGT DIST C: {dist_center:.1f}m", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Depth Radar (Right)
        cv2.putText(thermal_resized, "[DEPTH OBSTACLE RADAR]", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(thermal_resized, f"L: {dist_left:.1f}m | C: {dist_center:.1f}m | R: {dist_right:.1f}m", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Crosshairs
        cv2.drawMarker(annotated_rgb, (w // 2, h // 2), (0, 255, 0), markerType=cv2.MARKER_CROSS, markerSize=18, thickness=1)
        cv2.drawMarker(thermal_resized, (w // 2, h // 2), (0, 255, 255), markerType=cv2.MARKER_CROSS, markerSize=18, thickness=1)

        hud = np.hstack((annotated_rgb, thermal_resized))
        cv2.imshow("Autonomous Surveillance & Avoidance Station", hud)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("[TACTICAL RECON] Operator commanded RTB.")
        break

# Landing Sequence
cv2.destroyAllWindows()
client.moveToPositionAsync(0, 0, CRUISE_ALTITUDE, 3).join()
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("[TACTICAL RECON] Drone secured.")