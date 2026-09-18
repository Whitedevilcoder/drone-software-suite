import airsim
import time
import numpy as np
from config import *

class FlightController:
    def __init__(self, client):
        self.client = client
        self.current_wp_idx = 0
        self.active_mode = "PATROL"
        self.target_lost_time = time.time()
        self.last_cmd_time = 0
        self.evasion_start_time = 0  # NEW: Tracks how long we've been evading
        self.evasion_dir = 1         # NEW: Locks the evasion direction (-1 or 1)
        
    def navigate_to_wp(self, idx):
        tx, ty, tz = WAYPOINTS[idx]
        print(f"\n[NAV CORE] Advancing to Sector {idx + 1}/{len(WAYPOINTS)}")
        self.client.moveToPositionAsync(
            tx, ty, tz, PATROL_SPEED, 
            drivetrain=airsim.DrivetrainType.ForwardOnly, 
            yaw_mode=airsim.YawMode(False, 0)
        )

    def update_state(self, pos, yaw_rad, dist_L, dist_C, dist_R, target_cx, error_x, frame_width):
        curr_time = time.time()
        
        # 1. EVASION TRIGGER LOGIC
        # If we see an obstacle AND we aren't already locked in an evasion...
        if (dist_C < OBSTACLE_TRIGGER_DIST or dist_L < 3.0 or dist_R < 3.0) and self.active_mode != "EVADING":
            print(f"\n[NAV CORE] Obstacle Detected! (L:{dist_L:.1f} C:{dist_C:.1f} R:{dist_R:.1f}) Canceling patrol to evade.")
            self.client.cancelLastTask()
            self.active_mode = "EVADING"
            self.evasion_start_time = curr_time
            # Lock in the direction that has more space
            self.evasion_dir = 1.0 if dist_R > dist_L else -1.0 
            
        # 2. EVASION EXECUTION LOGIC
        if self.active_mode == "EVADING":
            # COMMITMENT CHECK: Must dodge for at least 1.5s AND center must be clear
            if (curr_time - self.evasion_start_time) > 1.5 and dist_C > (OBSTACLE_TRIGGER_DIST + 2.0):
                print("\n[NAV CORE] Obstacle Cleared. Resuming standard logic.")
                self.active_mode = "PATROL" # Exit evasion
                self.navigate_to_wp(self.current_wp_idx)
                return True
                
            # Continue dodging laterally
            vy_body = 3.5 * self.evasion_dir 
            vx_world = float(1.0 * np.cos(yaw_rad) - vy_body * np.sin(yaw_rad))
            vy_world = float(1.0 * np.sin(yaw_rad) + vy_body * np.cos(yaw_rad))
            
            if (curr_time - self.last_cmd_time) > CMD_INTERVAL:
                self.client.moveByVelocityZAsync(vx_world, vy_world, CRUISE_ALTITUDE, 0.3)
                self.last_cmd_time = curr_time
                
        # 3. TARGET TRACKING LOGIC (Only runs if NOT evading)
        elif target_cx is not None:
            if self.active_mode != "TARGET_LOCK":
                print("\n[TACTICAL AI] Initiating Target Pursuit.")
                self.client.cancelLastTask()
                self.active_mode = "TARGET_LOCK"
                self.target_lost_time = curr_time
            
            yaw_rate = float(np.clip(0.08 * (error_x / (frame_width // 2)) * 30.0, -25.0, 25.0))
            vx_cmd = float(1.5 * np.cos(yaw_rad))
            vy_cmd = float(1.5 * np.sin(yaw_rad))
            
            if (curr_time - self.last_cmd_time) > CMD_INTERVAL:
                self.client.moveByVelocityZAsync(
                    vx_cmd, vy_cmd, CRUISE_ALTITUDE, 0.3, 
                    airsim.DrivetrainType.MaxDegreeOfFreedom, 
                    airsim.YawMode(True, yaw_rate)
                )
                self.last_cmd_time = curr_time
                
        # 4. PATROL LOGIC
        else:
            if self.active_mode != "PATROL":
                if self.active_mode == "TARGET_LOCK" and (curr_time - self.target_lost_time) <= 3.0:
                    pass # Coasting
                else:
                    self.client.cancelLastTask()
                    self.active_mode = "PATROL"
                    self.navigate_to_wp(self.current_wp_idx)
                    return True 

            if self.active_mode == "PATROL":
                tx, ty, _ = WAYPOINTS[self.current_wp_idx]
                if np.sqrt((pos.x_val - tx)**2 + (pos.y_val - ty)**2) < 2.5:
                    self.current_wp_idx = (self.current_wp_idx + 1) % len(WAYPOINTS)
                    self.navigate_to_wp(self.current_wp_idx)
        
        return False