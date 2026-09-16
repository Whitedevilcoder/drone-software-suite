import airsim
import cv2
import numpy as np
import time
import sys
from config import *
from vision_module import ReconVision
from flight_core import FlightController

import msgpackrpc, pathlib

p = pathlib.Path(msgpackrpc.__file__).parent / "transport" / "tcp.py"
src = p.read_text()

old = "self._unpacker = msgpack.Unpacker(encoding=encodings[1])"
new = "self._unpacker = msgpack.Unpacker(encoding=encodings[1], max_buffer_size=200*1024*1024)"

if old in src:
    p.write_text(src.replace(old, new))
    print("Patched:", p)
elif "max_buffer_size" in src:
    print("Already patched:", p)
else:
    print("Pattern not found. Lines containing 'Unpacker(':")
    for i, line in enumerate(src.splitlines(), 1):
        if "Unpacker(" in line:
            print(i, repr(line))

def main():
    try:
        # 1. System Initialization
        vision = ReconVision()
        client = airsim.MultirotorClient()
        client.confirmConnection()
        client.enableApiControl(True)
        client.armDisarm(True)
        client.cancelLastTask()

        flight = FlightController(client)

        cv2.namedWindow("Autonomous Tactical Station", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Autonomous Tactical Station", 1280, 520)

        print("[TACTICAL RECON] Launching...")
        client.takeoffAsync().join()
        client.moveToZAsync(CRUISE_ALTITUDE, 2).join()
        time.sleep(1)

        flight.navigate_to_wp(flight.current_wp_idx)
        last_frame_time = time.time()

        while True:
            try:
                # Telemetry Pipeline with Safety Guards
                state = client.getMultirotorState()
                pos = state.kinematics_estimated.position
                orientation = state.kinematics_estimated.orientation
                yaw_rad = airsim.to_eularian_angles(orientation)[2]
                alt = -pos.z_val
                vx = state.kinematics_estimated.linear_velocity.x_val
                vy = state.kinematics_estimated.linear_velocity.y_val
                speed_ms = np.sqrt(vx**2 + vy**2)
                
                # Request compressed images to stay safely under msgpack 1MB limit
                responses = client.simGetImages([
                    airsim.ImageRequest("front_center", airsim.ImageType.Scene, False, True),
                    airsim.ImageRequest("front_center", airsim.ImageType.DepthPerspective, True, False)
                ])

                if len(responses) >= 2 and responses[0].width > 0:
                    curr_time = time.time()
                    fps = 1.0 / (curr_time - last_frame_time + 1e-5)
                    last_frame_time = curr_time

                    # Decode frame safely
                    frame_rgb = vision.decode_frame(responses[0])
                    if frame_rgb is None or frame_rgb.size == 0:
                        continue
                        
                    h, w = frame_rgb.shape[:2]
                    
                    # Perception Pipeline
                    dist_L, dist_C, dist_R, thermal_img = vision.process_depth(responses[1])
                    annotated_rgb, target_cx, target_cy, error_x = vision.detect_and_track(frame_rgb, pos, alt, speed_ms)
                    
                    # Flight Control Pipeline
                    reset_tracker = flight.update_state(pos, yaw_rad, alt, dist_L, dist_C, dist_R, target_cx, error_x, w)
                    if reset_tracker:
                        vision.active_target_id = -1
                        
                    # Telemetry HUD
                    thermal_resized = cv2.resize(thermal_img, (w, h))
                    mode_color = (0, 0, 255) if flight.active_mode != "PATROL" else (0, 255, 0)
                    
                    cv2.putText(annotated_rgb, f"STATUS: {flight.active_mode}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
                    cv2.putText(annotated_rgb, f"ALT: {alt:.1f}m | SPD: {speed_ms:.1f}m/s | FPS: {fps:.0f}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    cv2.drawMarker(annotated_rgb, (w // 2, h // 2), (0, 255, 0), cv2.MARKER_CROSS, 18, 1)
                    cv2.drawMarker(thermal_resized, (w // 2, h // 2), (0, 255, 255), cv2.MARKER_CROSS, 18, 1)
                    
                    cv2.imshow("Autonomous Tactical Station", np.hstack((annotated_rgb, thermal_resized)))
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("[TACTICAL RECON] Operator commanded RTB.")
                        break
                    
                    time.sleep(0.03)

            except Exception as inner_e:
                # Catch frame-level exceptions so the core loop never dies
                print(f"[WARNING] Loop exception caught: {inner_e}")
                time.sleep(0.1)
                continue

    except Exception as e:
        print(f"[CRITICAL ERROR] Mission failure: {e}")
    finally:
        try:
            cv2.destroyAllWindows()
            client.moveToPositionAsync(0, 0, CRUISE_ALTITUDE, 3).join()
            client.landAsync().join()
            client.armDisarm(False)
            client.enableApiControl(False)
            print("Drone secured safely.")
        except Exception:
            pass

if __name__ == "__main__":
    main()