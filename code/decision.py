import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):
    # Handling loops.
    if Rover.mode == "loop":
        # Stop steering, keep moving for two seconds, then exit the loop state.
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        Rover.loop_counter += 1
        if Rover.loop_counter >= 50:
            Rover.mode = 'forward'
            Rover.loop_counter = 0
        return Rover
    
    # Keeping track of how much we have been moving left/right to break loops.
    if abs(Rover.steer) >= 7:
        Rover.steering_counter += 1
        
        # If the car is steering for 300 frames, then it is stuck in a loop.
        if Rover.steering_counter >= 300: # About 5 seconds
            Rover.mode = "loop"
            Rover.steering_counter = 0
            return Rover
    else:
        Rover.steering_counter = 0
    
    
    # Handling when the car is stuck by some obstacle.
    if Rover.mode == 'stuck':
        # Try full throttle for two seconds to get over obstacles.
        if Rover.stuck_mode == 'forward':
            Rover.throttle = 1
            Rover.stuck_counter += 1
            
            # If the car is still stuck, change from moving to steering.
            if Rover.stuck_counter >= 120:
                Rover.stuck_mode = 'steer'
                Rover.stuck_counter = 0
        
        elif Rover.stuck_mode == 'steer':
            Rover.throttle = 0
            Rover.steer = -15 # Steer right
            Rover.stuck_counter += 1
            
            # If the car is still stuck, change to moving and steering.
            if Rover.stuck_counter >= 120:
                Rover.stuck_mode = 'forward-steer'
                Rover.stuck_counter = 0
        
        elif Rover.stuck_mode == 'forward-steer':
            Rover.throttle = 1
            Rover.steer = -15 # Steer right
            Rover.stuck_counter += 1
            
            # If the car is still stuck, repeat again from just moving.
            if Rover.stuck_counter >= 120:
                Rover.stuck_mode = 'forward'
                Rover.stuck_counter = 0
        if Rover.vel >= 0.5:
            Rover.mode = 'forward'
            Rover.stuck_mode = ''
            Rover.stuck_counter = 0
        return Rover
    
    # Checking if the car is stuck by some obstacle while moving.
    if Rover.mode == 'forward' and Rover.vel < 0.5:
        Rover.stuck_counter += 1
        
        # If the car is stuck for 2 seconds, then it is in a 'stuck' state.
        if Rover.stuck_counter >= 120:
            Rover.mode = 'stuck'
            Rover.stuck_mode = 'forward'
            Rover.stuck_counter = 0
    else:
        Rover.stuck_counter = 0
    
    
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

