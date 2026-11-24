import airsim
import cv2
import numpy as np
import time
import sys
from config import *
from vision_module import ReconVision
from flight_core import FlightController

def main():
    try:
        # 1. LOAD AI & WARMUP 
        vision = ReconVision()
        print("[TACTICAL AI] Warming up CUDA pipelines...")
        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        vision.model.track(source=dummy_frame, verbose=False, device=USE_DEVICE)
        print("[TACTICAL AI] Ready.")

        # 2. CONNECT TO SIMULATOR
        print("[NAV CORE] Establishing link with AirSim...")
        client = airsim.MultirotorClient()
        client.confirmConnection()
        client.enableApiControl(True)
        client.armDisarm(True)
        client.cancelLastTask()

        flight = FlightController(client)

        cv2.namedWindow("Autonomous Tactical Station", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Autonomous Tactical Station", 1280, 520)

        print("[NAV CORE] Launching...")
        client.takeoffAsync().join()
        client.moveToZAsync(CRUISE_ALTITUDE, 2).join()
        time.sleep(1)

        flight.navigate_to_wp(flight.current_wp_idx)
        last_frame_time = time.time()

        while True:
            try:
                # Watchdog: Re-assert control if AirSim drops it
                if not client.isApiControlEnabled():
                    client.enableApiControl(True)

                state = client.getMultirotorState()
                pos = state.kinematics_estimated.position
                yaw_rad = airsim.to_eularian_angles(state.kinematics_estimated.orientation)[2]
                alt = -pos.z_val
                vx = state.kinematics_estimated.linear_velocity.x_val
                vy = state.kinematics_estimated.linear_velocity.y_val
                speed_ms = np.sqrt(vx**2 + vy**2)
                
                responses = client.simGetImages([
                    airsim.ImageRequest("front_center", airsim.ImageType.Scene, False, True),
                    airsim.ImageRequest("front_center", airsim.ImageType.DepthPerspective, True, False)
                ])

                if len(responses) >= 2 and responses[0].width > 0 and responses[1].width > 0:
                    curr_time = time.time()
                    fps = 1.0 / (curr_time - last_frame_time + 1e-5)
                    last_frame_time = curr_time

                    frame_rgb = vision.decode_frame(responses[0])
                    if frame_rgb is None: continue
                    h, w = frame_rgb.shape[:2]
                    
                    # Execution Pipeline
                    dist_L, dist_C, dist_R, thermal_img = vision.process_depth(responses[1])
                    
                    # Unpack the new active_class variable here
                    annotated_rgb, target_cx, target_cy, error_x, active_class = vision.detect_and_track(frame_rgb, pos, alt, speed_ms)
                    
                    reset_tracker = flight.update_state(pos, yaw_rad, dist_L, dist_C, dist_R, target_cx, error_x, w)
                    if reset_tracker:
                        vision.active_target_id = -1
                        
                    # DYNAMIC HUD RENDERING
                    thermal_resized = cv2.resize(thermal_img, (w, h), interpolation=cv2.INTER_NEAREST)
                    mode_color = (0, 0, 255) if flight.active_mode != "PATROL" else (0, 255, 0)
                    
                    cv2.putText(annotated_rgb, f"STATUS: {flight.active_mode}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
                    cv2.putText(annotated_rgb, f"SECTOR: {flight.current_wp_idx + 1}/4 | ALT: {alt:.1f}m | SPD: {speed_ms:.1f}m/s | FPS: {fps:.0f}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    cv2.putText(thermal_resized, f"RADAR L: {dist_L:.1f}m | C: {dist_C:.1f}m | R: {dist_R:.1f}m", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                    cv2.drawMarker(annotated_rgb, (w // 2, h // 2), (0, 255, 0), cv2.MARKER_CROSS, 18, 1)
                    cv2.drawMarker(thermal_resized, (w // 2, h // 2), (0, 255, 255), cv2.MARKER_CROSS, 18, 1)
                    
                    cv2.imshow("Autonomous Tactical Station", np.hstack((annotated_rgb, thermal_resized)))
                    
                    # LIVE TERMINAL TELEMETRY STREAM (Updated to show Target Lock)
                    lock_str = f"{active_class}-{vision.active_target_id}" if vision.active_target_id != -1 else "CLEAR"
                    sys.stdout.write(f"\r[TELEMETRY] MODE: {flight.active_mode:<11} | ALT: {alt:5.1f}m | SPD: {speed_ms:4.1f}m/s | TGT LOCK: {lock_str:<12} | FPS: {fps:3.0f}")
                    sys.stdout.flush()

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\n[NAV CORE] Operator commanded RTB.")
                        break
                    
                    time.sleep(0.01)

            except Exception as inner_e:
                print(f"\n[WARNING] Loop exception caught: {inner_e}")
                time.sleep(0.1)
                continue

    except KeyboardInterrupt:
        print("\n[NAV CORE] Mission aborted by operator.")
    except Exception as e:
        print(f"\n[CRITICAL FAULT] System failure: {e}")
    finally:
        try:
            print("\n[NAV CORE] Securing drone...")
            cv2.destroyAllWindows()
            client.moveToPositionAsync(0, 0, CRUISE_ALTITUDE, 3).join()
            client.landAsync().join()
            client.armDisarm(False)
            client.enableApiControl(False)
            print("[NAV CORE] Drone secured.")
        except Exception:
            pass

if __name__ == "__main__":
    main()