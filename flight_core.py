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
        
    def navigate_to_wp(self, idx):
        tx, ty, tz = WAYPOINTS[idx]
        print(f"[NAV CORE] Advancing to Sector {idx + 1}/{len(WAYPOINTS)}")
        self.client.moveToPositionAsync(
            tx, ty, tz, PATROL_SPEED, 
            drivetrain=airsim.DrivetrainType.ForwardOnly, 
            yaw_mode=airsim.YawMode(False, 0)
        )

    def update_state(self, pos, yaw_rad, alt, dist_L, dist_C, dist_R, target_cx, error_x, frame_width):
        curr_time = time.time()
        
        # 1. EVASION LOGIC (Highest Priority)
        if dist_C < OBSTACLE_TRIGGER_DIST or dist_L < 3.0 or dist_R < 3.0:
            self.active_mode = "EVADING"
            vy_body = 2.0 if dist_L < dist_R else -2.0
            vx_world = float(-0.5 * np.cos(yaw_rad) - vy_body * np.sin(yaw_rad))
            vy_world = float(-0.5 * np.sin(yaw_rad) + vy_body * np.cos(yaw_rad))
            
            # Rate-limited execution to prevent API flooding
            if (curr_time - self.last_cmd_time) > CMD_INTERVAL:
                self.client.moveByVelocityZAsync(vx_world, vy_world, CRUISE_ALTITUDE, 0.3)
                self.last_cmd_time = curr_time
                
        # 2. TARGET TRACKING LOGIC
        elif target_cx is not None:
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
                
        # 3. PATROL LOGIC
        else:
            if self.active_mode != "PATROL":
                if self.active_mode == "TARGET_LOCK" and (curr_time - self.target_lost_time) <= 3.0:
                    pass # Coasting mode: hold trajectory while searching for lost target
                else:
                    self.active_mode = "PATROL"
                    self.navigate_to_wp(self.current_wp_idx)
                    return True # Signal the main loop to clear the vision tracker ID

            if self.active_mode == "PATROL":
                tx, ty, _ = WAYPOINTS[self.current_wp_idx]
                if np.sqrt((pos.x_val - tx)**2 + (pos.y_val - ty)**2) < 2.5:
                    self.current_wp_idx = (self.current_wp_idx + 1) % len(WAYPOINTS)
                    self.navigate_to_wp(self.current_wp_idx)
        
        return False