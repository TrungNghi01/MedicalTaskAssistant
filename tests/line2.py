import picar_4wd as fc
import cv2
import numpy as np
import time
import os
import subprocess

class LineFollower:
    def __init__(self):
        self.camera_available = False
        self.cap = None
        self.initialize_camera()
        
        # Line following parameters
        self.last_error = 0
        self.max_speed = 10  # Maximum speed value
        
        # PID controller parameters (tune these values)
        self.kp = 0.5  # Proportional gain
        self.kd = 0.1  # Derivative gain
        
        # Line detection parameters
        self.lower_threshold = np.array([0, 0, 0])  # Lower threshold for black line
        self.upper_threshold = np.array([255, 107, 94])  # Upper threshold for black line
    
    def initialize_camera(self):
        """Initialize camera with detailed diagnostics"""
        print("\n=== Camera Diagnostics ===")
        
        # Check for camera devices
        try:
            camera_ls = subprocess.check_output("ls -l /dev/video*", shell=True).decode('utf-8')
            print(f"Available camera devices:\n{camera_ls}")
        except:
            print("No camera devices found at /dev/video*")
        
        # Check if any process is using the camera
        
        # Check camera module is enabled in raspi-config
        try:
            with open('/boot/config.txt', 'r') as f:
                config = f.read()
                if 'start_x=1' in config:
                    print("Camera module is enabled in raspi-config")
                else:
                    print("WARNING: Camera might not be enabled in raspi-config")
        except:
            print("Could not check if camera is enabled in raspi-config")
        
        # Try to kill any process that might be using the camera
        try:
            os.system("sudo fuser -k /dev/video0 2>/dev/null")
            print("Killed any processes using the camera")
        except:
            pass
        
        # Force release any previous camera instance
        if self.cap is not None:
            try:
                self.cap.release()
                print("Released previous camera instance")
            except:
                pass
        
        print("Waiting 2 seconds for camera resources to be released...")
        time.sleep(2)
        
        # Try a simple capture first
        try:
            print("Testing simple camera capture...")
            test_cap = cv2.VideoCapture(0)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                test_cap.release()
                if ret:
                    print("Simple camera test succeeded!")
                else:
                    print("Simple camera test failed - could not grab frame")
            else:
                print("Simple camera test failed - could not open camera")
        except Exception as e:
            print(f"Simple camera test exception: {e}")
        
        # Now try the actual camera setup for line following
        print("Initializing camera for line following...")
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                print("Failed to open camera with cv2.CAP_V4L2")
                print("Trying without V4L2 flag...")
                self.cap = cv2.VideoCapture(0)
                
            if not self.cap.isOpened():
                print("ERROR: Could not open camera with any method")
                self.camera_available = False
            else:
                # Try reading a frame
                ret, frame = self.cap.read()
                if ret:
                    print(f"Successfully grabbed a frame of size {frame.shape}")
                    # Try setting resolution
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
                    
                    # Verify the resolution was set
                    width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    print(f"Camera resolution set to {width}x{height}")
                    
                    self.camera_available = True
                    print("Camera initialized successfully!")
                else:
                    print("ERROR: Camera opened but could not grab frame")
                    self.camera_available = False
        except Exception as e:
            print(f"Camera initialization error: {e}")
            self.camera_available = False
        
        print("=== End of Camera Diagnostics ===\n")
        return self.camera_available
        
    def detect_line(self, frame):
        if frame is None:
            return None, None
            
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask for black line
            mask = cv2.inRange(hsv, self.lower_threshold, self.upper_threshold)
            
            # Crop the bottom portion of the frame (where the line is most likely to be)
            height, width = mask.shape
            crop_height = int(height * 0.5)  # Use bottom 50% of image
            roi = mask[height - crop_height:height, 0:width]
            
            # Find contours in the ROI
            contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Draw region of interest on original frame for visualization
            cv2.rectangle(frame, (0, height - crop_height), (width, height), (0, 255, 0), 2)
            
            if contours:
                # Find the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Calculate the centroid of the contour
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"]) + (height - crop_height)  # Adjust y-coordinate to original frame
                    
                    # Draw centroid on the frame
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    
                    # Calculate the error (distance from center of frame)
                    error = cx - (width // 2)
                    return frame, error
                
            return frame, None
        except Exception as e:
            print(f"Error in detect_line: {e}")
            return None, None
    
    def follow_line(self):
        try:
            if not self.camera_available:
                print("Camera not available, using fallback movement pattern")
                self.fallback_movement()
                return
                
            fail_counter = 0
            frame_counter = 0
            
            while True:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    fail_counter += 1
                    print(f"Failed to grab frame (attempt {fail_counter}/5)")
                    
                    if fail_counter >= 5:
                        print("Multiple failures to grab frames, reinitializing camera...")
                        self.cap.release()
                        time.sleep(1)
                        self.initialize_camera()
                        fail_counter = 0
                        
                        if not self.camera_available:
                            print("Camera reinitialization failed, using fallback movement")
                            self.fallback_movement()
                            return
                    
                    time.sleep(0.5)
                    continue
                
                # Reset fail counter on successful frame
                fail_counter = 0
                frame_counter += 1
                
                # Save a sample frame occasionally for debugging
                if frame_counter % 30 == 0:
                    try:
                        cv2.imwrite(f'debug_frame_{frame_counter}.jpg', frame)
                        print(f"Saved debug frame {frame_counter}")
                    except Exception as e:
                        print(f"Could not save debug frame: {e}")
                
                # Detect line and calculate error
                frame, error = self.detect_line(frame)
                
                if error is not None:
                    # Calculate derivative of error (change in error)
                    error_derivative = error - self.last_error
                    self.last_error = error
                    
                    # PID control (using only P and D terms here)
                    correction = self.kp * error + self.kd * error_derivative
                    
                    # Decide direction based on correction value
                    if abs(error) < 20:  # Line is approximately centered
                        print("Moving forward")
                        fc.forward(self.max_speed)
                    elif error < 0:  # Line is to the left
                        print(f"Turning left, error: {error}")
                        fc.turn_left(self.max_speed)
                    else:  # Line is to the right
                        print(f"Turning right, error: {error}")
                        fc.turn_right(self.max_speed)
                else:
                    # No line detected
                    print("No line detected, stopping")
                    fc.stop()
                
                # Display the processed frame if not None
                if frame is not None:
                    try:
                        cv2.imshow('Line Following', frame)
                        
                        # Break the loop on 'q' key press
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    except Exception as e:
                        print(f"Error displaying frame: {e}")
                
                # Add small delay
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Error in follow_line: {e}")
        finally:
            # Clean up
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            fc.stop()
    
    def fallback_movement(self):
        """Simple movement pattern when camera isn't working"""
        try:
            print("Starting fallback movement pattern")
            counter = 0
            
            while True:
                counter += 1
                pattern = counter % 4
                
                if pattern == 0:
                    print("Moving forward")
                    fc.forward(self.max_speed)
                    time.sleep(1)
                elif pattern == 1:
                    print("Turning left")
                    fc.turn_left(self.max_speed)
                    time.sleep(0.5)
                elif pattern == 2:
                    print("Moving forward")
                    fc.forward(self.max_speed)
                    time.sleep(1)
                else:
                    print("Turning right")
                    fc.turn_right(self.max_speed)
                    time.sleep(0.5)
                
                # Short pause
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Fallback movement interrupted")
        finally:
            fc.stop()
            
    def update_thresholds(self, lower, upper):
        """Update the color thresholds for line detection"""
        self.lower_threshold = np.array(lower)
        self.upper_threshold = np.array(upper)
        print(f"Updated thresholds - Lower: {lower}, Upper: {upper}")
            
if __name__ == "__main__":
    # Create and run the line follower
    line_follower = LineFollower()
    
    # Use calibrated values if available
    # line_follower.update_thresholds([0, 0, 0], [179, 50, 100])
    
    line_follower.follow_line()
    print("Line following complete")