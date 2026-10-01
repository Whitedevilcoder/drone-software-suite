import cosysairsim as airsim
import cv2
import numpy as np
import time
import threading
import math  # NEW

# ----------------- CONFIGURATION -----------------
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
CENTER_X = IMAGE_WIDTH // 2
CENTER_Y = IMAGE_HEIGHT // 2

INTERCEPTOR_NAME = "Interceptor"
TARGET_NAME = "TargetDrone"

CLOSING_SPEED   = 35.0   # max forward speed
NAV_GAIN        = 4.2
SEARCH_YAW_RATE = 35.0

STANDOFF_DISTANCE = 2.0  # NEW: desired follow gap in meters
DIST_GAIN         = 2.5  # NEW: proportional gain for standoff control

KEY_UP    = 2490368
KEY_DOWN  = 2621440
KEY_LEFT  = 2424832
KEY_RIGHT = 2555904

# ----------------- INITIALIZATION -----------------
print("[*] Connecting to AirSim RPC...")
client = airsim.MultirotorClient()
client.confirmConnection()

for name in [INTERCEPTOR_NAME, TARGET_NAME]:
    client.enableApiControl(True, vehicle_name=name)
    client.armDisarm(True, vehicle_name=name)

client.simAddDetectionFilterMeshName("fpv_cam", airsim.ImageType.Scene, "TargetDrone*", vehicle_name=INTERCEPTOR_NAME)
client.simSetDetectionFilterRadius("fpv_cam", airsim.ImageType.Scene, 200 * 100, vehicle_name=INTERCEPTOR_NAME)

print("[*] Taking off into engagement airspace...")
f1 = client.takeoffAsync(vehicle_name=INTERCEPTOR_NAME)
f2 = client.takeoffAsync(vehicle_name=TARGET_NAME)
f1.join()
f2.join()

client.moveToPositionAsync(0.0,  0.0, -5.0, 3.0, vehicle_name=INTERCEPTOR_NAME).join()
client.moveToPositionAsync(25.0, 0.0, -5.0, 3.0, vehicle_name=TARGET_NAME).join()

# ----------------- SHARED STATE -----------------
sim_running = True
locked = False
cmd_vx, cmd_vy, cmd_vz, cmd_yaw_rate = 0.0, 0.0, 0.0, 0.0


def target_flight_routine():
    target_client = airsim.MultirotorClient()
    target_client.confirmConnection()
    direction = 1.0
    while sim_running:
        target_client.moveByVelocityAsync(
            vx=1.5, vy=4.0 * direction, vz=0.0,
            duration=3.0, vehicle_name=TARGET_NAME
        ).join()
        direction *= -1.0

threading.Thread(target=target_flight_routine, daemon=True).start()


def flight_heartbeat():
    ctrl_client = airsim.MultirotorClient()
    ctrl_client.confirmConnection()
    while sim_running:
        ctrl_client.moveByVelocityBodyFrameAsync(
            vx=cmd_vx, vy=cmd_vy, vz=cmd_vz, duration=0.03,
            yaw_mode=airsim.YawMode(is_rate=True, yaw_or_rate=cmd_yaw_rate),
            vehicle_name=INTERCEPTOR_NAME
        ).join()
        time.sleep(0.01)

threading.Thread(target=flight_heartbeat, daemon=True).start()

# ----------------- GUIDANCE LOOP -----------------
cv2.namedWindow("FPV Terminal Guidance - Wide FOV APN", cv2.WINDOW_NORMAL)

prev_los        = None
prev_time       = time.time()
lost_counter    = 0
last_target_pos = None

print("\n" + "="*60)
print(" COORDINATED APN TERMINAL SYSTEM ACTIVE")
print("="*60)
print("  SPACEBAR     : ENGAGE INTERCEPTOR RUN")
print("  ARROW KEYS   : MANUAL POSITIONING")
print("  ESC          : EXIT")
print("="*60 + "\n")

try:
    while True:
        responses = client.simGetImages([
            airsim.ImageRequest("fpv_cam", airsim.ImageType.Scene, False, False)
        ], vehicle_name=INTERCEPTOR_NAME)

        if not responses or responses[0].width == 0:
            continue

        now = time.time()
        dt = max(now - prev_time, 1e-4)
        prev_time = now

        raw_rgb = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
        frame = raw_rgb.reshape(responses[0].height, responses[0].width, 3).copy()

        detections = client.simGetDetections("fpv_cam", airsim.ImageType.Scene, vehicle_name=INTERCEPTOR_NAME)

        target_box    = None
        target_center = None

        if detections:
            d     = detections[0]
            box2d = d.box2D
            x_min = int(box2d.min.x_val)
            y_min = int(box2d.min.y_val)
            x_max = int(box2d.max.x_val)
            y_max = int(box2d.max.y_val)
            target_box    = (x_min, y_min, x_max - x_min, y_max - y_min)
            target_center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)

        key_raw = cv2.waitKeyEx(1)
        key     = key_raw & 0xFF

        if key == 27:
            break
        elif key == 32:  # SPACEBAR toggle
            locked       = not locked
            prev_los     = None
            lost_counter = 0
            last_target_pos = None
            if locked:
                print("[!] TERMINAL RAM ENGAGED")
            else:
                print("[!] MANUAL MODE")
                cmd_vx, cmd_vy, cmd_vz, cmd_yaw_rate = 0.0, 0.0, 0.0, 0.0

        # ----------------- TERMINAL APN WITH LATERAL DRAFT -----------------
        if locked:
            if target_center is not None:
                # ============================================================
                # MODE 1 — VISUAL APN (camera tracking)
                # ============================================================
                lost_counter = 0
                cx, cy = target_center

                los_az = (cx - CENTER_X) / CENTER_X
                los_el = (cy - CENTER_Y) / CENTER_Y
                current_los = np.array([los_az, los_el])

                if prev_los is not None:
                    omega = (current_los - prev_los) / dt
                    cmd_yaw_rate = float(np.clip(NAV_GAIN * omega[0] * 57.3 + los_az * 25.0, -70.0, 70.0))
                    cmd_vz       = float(np.clip(NAV_GAIN * omega[1] * CLOSING_SPEED + los_el * 4.0, -5.5, 5.5))
                else:
                    cmd_yaw_rate = float(np.clip(los_az * 40.0, -40.0, 40.0))
                    cmd_vz       = float(np.clip(los_el * 3.5, -3.5, 3.5))

                cmd_vy  = float(np.clip(los_az * 10.0, -8.0, 8.0))
                prev_los = current_los

                # cache target world position + compute standoff distance
                try:
                    tp = client.simGetObjectPose(TARGET_NAME)
                    last_target_pos = (tp.position.x_val, tp.position.y_val, tp.position.z_val)

                    # NEW: distance-based forward speed instead of flat CLOSING_SPEED
                    istate = client.getMultirotorState(vehicle_name=INTERCEPTOR_NAME)
                    ipos   = istate.kinematics_estimated.position
                    dist = math.sqrt(
                        (last_target_pos[0] - ipos.x_val) ** 2 +
                        (last_target_pos[1] - ipos.y_val) ** 2 +
                        (last_target_pos[2] - ipos.z_val) ** 2
                    )
                    cmd_vx = float(np.clip(DIST_GAIN * (dist - STANDOFF_DISTANCE), -CLOSING_SPEED, CLOSING_SPEED))

                    cv2.putText(frame, f"RANGE: {dist:.1f} m", (20, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                except Exception:
                    cmd_vx = CLOSING_SPEED  # fallback if pose fetch fails

                x, y, w, h = target_box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(frame, (int(cx), int(cy)), 4, (0, 0, 255), -1)
                cv2.line(frame, (CENTER_X, CENTER_Y), (int(cx), int(cy)), (0, 0, 255), 2)

            else:
                # ============================================================
                # MODE 2 — TARGET OUT OF FOV — 3-D pursuit
                # ============================================================
                lost_counter += 1
                prev_los = None

                try:
                    tp = client.simGetObjectPose(TARGET_NAME)
                    last_target_pos = (tp.position.x_val, tp.position.y_val, tp.position.z_val)
                except Exception:
                    pass

                if last_target_pos is not None:
                    istate = client.getMultirotorState(vehicle_name=INTERCEPTOR_NAME)
                    ipos   = istate.kinematics_estimated.position
                    iquat  = istate.kinematics_estimated.orientation

                    dx = last_target_pos[0] - ipos.x_val
                    dy = last_target_pos[1] - ipos.y_val
                    dz = last_target_pos[2] - ipos.z_val
                    dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)  # NEW

                    yaw = math.atan2(
                        2.0 * (iquat.w_val * iquat.z_val + iquat.x_val * iquat.y_val),
                        1.0 - 2.0 * (iquat.y_val ** 2 + iquat.z_val ** 2)
                    )

                    bearing = math.atan2(dy, dx)
                    rel_yaw = math.atan2(math.sin(bearing - yaw), math.cos(bearing - yaw))

                    # NEW: forward speed now driven by standoff error, not a flat constant
                    speed = float(np.clip(DIST_GAIN * (dist - STANDOFF_DISTANCE), -CLOSING_SPEED, CLOSING_SPEED))

                    cmd_vx       = float(np.clip(speed * math.cos(rel_yaw), -CLOSING_SPEED, CLOSING_SPEED))
                    cmd_vy       = float(np.clip(speed * math.sin(rel_yaw), -CLOSING_SPEED, CLOSING_SPEED))
                    cmd_vz       = float(np.clip(dz * 2.5, -6.0, 6.0))
                    cmd_yaw_rate = float(np.clip(math.degrees(rel_yaw) * 2.5, -60.0, 60.0))

                    cv2.putText(frame, f"3D PURSUIT - RANGE {dist:.1f} m", (20, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

                else:
                    cmd_vx, cmd_vy, cmd_vz = 0.0, 0.0, 0.0
                    cmd_yaw_rate = SEARCH_YAW_RATE
                    cv2.putText(frame, "SCANNING FOR TARGET...", (20, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        else:
            cmd_vx, cmd_vy, cmd_vz, cmd_yaw_rate = 0.0, 0.0, 0.0, 0.0
            if key == ord('w'):   cmd_vx = 10.0
            elif key == ord('s'): cmd_vx = -10.0
            if key == ord('d'):   cmd_vy = 6.0
            elif key == ord('a'): cmd_vy = -6.0

            if   key_raw == KEY_UP   or key == ord('r'): cmd_vz = -3.5
            elif key_raw == KEY_DOWN or key == ord('f'): cmd_vz =  3.5
            if   key_raw == KEY_LEFT or key == ord('q'): cmd_yaw_rate = -40.0
            elif key_raw == KEY_RIGHT or key == ord('e'): cmd_yaw_rate = 40.0

            if target_box is not None:
                x, y, w, h = target_box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.circle(frame, (int(target_center[0]), int(target_center[1])), 4, (0, 255, 255), -1)

        cv2.circle(frame, (CENTER_X, CENTER_Y), 22, (255, 255, 255), 1)
        cv2.line(frame, (CENTER_X - 16, CENTER_Y), (CENTER_X + 16, CENTER_Y), (255, 255, 255), 1)
        cv2.line(frame, (CENTER_X, CENTER_Y - 16), (CENTER_X, CENTER_Y + 16), (255, 255, 255), 1)

        if locked and target_center is not None:
            mode_label  = "TERMINAL HOMING  (APN)"
            status_color = (0, 0, 255)
        elif locked and last_target_pos is not None:
            mode_label  = "3D PURSUIT MODE"
            status_color = (0, 165, 255)
        elif locked:
            mode_label  = "SCANNING..."
            status_color = (0, 255, 255)
        else:
            mode_label  = "BORESIGHT ACQUIRED  (PRESS SPACE)"
            status_color = (0, 255, 0)

        cv2.putText(frame, f"STATUS: {mode_label}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)

        col = client.simGetCollisionInfo(vehicle_name=INTERCEPTOR_NAME)
        if col.has_collided:
            cv2.putText(frame, ">>> DIRECT IMPACT RECORDED <<<", (50, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2)

        cv2.imshow("FPV Terminal Guidance - Wide FOV APN", frame)

except KeyboardInterrupt:
    pass

sim_running = False
cv2.destroyAllWindows()
for name in [INTERCEPTOR_NAME, TARGET_NAME]:
    client.landAsync(vehicle_name=name)
    client.armDisarm(False, vehicle_name=name)
    client.enableApiControl(False, vehicle_name=name)