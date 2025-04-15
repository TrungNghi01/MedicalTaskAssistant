import picar_4wd as fc
import cv2
import numpy as np
import time

class LineFollower:
    def __init__(self):
        # Initialize camera
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Use 0 for default camera
        
        # Check if camera opened successfully
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            exit()
            
        # Set camera resolution (adjust as needed)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        
        # Line following parameters
        self.last_error = 0
        self.max_speed = 10  # Maximum speed value
        
        # PID controller parameters (tune these values)
        self.kp = 0.5  # Proportional gain
        self.kd = 0.1  # Derivative gain
        
        # Line detection parameters
        self.lower_threshold = np.array([0, 0, 0])  # Lower threshold for black line
        self.upper_threshold = np.array([255, 107, 94])  # Upper threshold for black line
        # self.upper_threshold = np.array([180, 50, 60])  # Upper threshold for black line
        
    def detect_line(self, frame):
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for black line
        mask = cv2.inRange(hsv, self.lower_threshold, self.upper_threshold)
        
        # Crop the bottom portion of the frame (where the line is most likely to be)
        height, width = mask.shape
        crop_height = int(height * 0.5)  # Use bottom 50% of image
        crop_width = int(width * 0.5)    # Use middle 50% of width

        # Calculate the start and end points to keep the ROI centered
        start_x = int((width - crop_width) / 2)
        end_x = start_x + crop_width
        
        roi = mask[height - crop_height:height, 0:width]
        
        # Find contours in the ROI
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw region of interest on original frame for visualization
        # cv2.rectangle(frame, (0, height - crop_height), (width, height), (0, 255, 0), 2)
        
        # Draw region of interest on original frame for visualization
        cv2.rectangle(frame, 
              (start_x, height - crop_height),  # Top-left point of rectangle
              (end_x, height),                  # Bottom-right point of rectangle
              (0, 255, 0), 2)                   # Green color, 2px thickness


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
    
    def follow_line(self):
        try:
            counter = 0
            while counter < 100:  # Run for a limited number of frames
            # while True:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
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
                        # fc.turn_left(min(abs(int(correction)), 100))
                    else:  # Line is to the right
                        print(f"Turning right, error: {error}")
                        fc.turn_right(self.max_speed)
                        # fc.turn_right(min(abs(int(correction)), 100))

                    counter = 0  # Reset counter if line is detected
                else:
                    # No line detected
                    print("No line detected, stopping")
                    fc.stop()
                    counter += 1 # Increment counter if no line detected
                
                # Display the processed frame
                cv2.imshow('Line Following', frame)
                
                # Break the loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                # Add small delay
                time.sleep(0.01)
                
        finally:
            # Clean up
            self.cap.release()
            cv2.destroyAllWindows()
            fc.stop()
            
if __name__ == "__main__":
    # Create and run the line follower
    line_follower = LineFollower()
    line_follower.follow_line()
    print("Active pill dispenser")
