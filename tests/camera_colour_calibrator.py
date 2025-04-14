import cv2
import numpy as np
import time

def calibrate_thresholds():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    def nothing(x):
        pass
    
    # Create window with trackbars
    cv2.namedWindow('Threshold Calibration')
    cv2.createTrackbar('H_low', 'Threshold Calibration', 0, 179, nothing)
    cv2.createTrackbar('S_low', 'Threshold Calibration', 0, 255, nothing)
    cv2.createTrackbar('V_low', 'Threshold Calibration', 0, 255, nothing)
    cv2.createTrackbar('H_high', 'Threshold Calibration', 179, 179, nothing)
    cv2.createTrackbar('S_high', 'Threshold Calibration', 255, 255, nothing)
    cv2.createTrackbar('V_high', 'Threshold Calibration', 255, 255, nothing)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Get trackbar positions
        h_low = cv2.getTrackbarPos('H_low', 'Threshold Calibration')
        s_low = cv2.getTrackbarPos('S_low', 'Threshold Calibration')
        v_low = cv2.getTrackbarPos('V_low', 'Threshold Calibration')
        h_high = cv2.getTrackbarPos('H_high', 'Threshold Calibration')
        s_high = cv2.getTrackbarPos('S_high', 'Threshold Calibration')
        v_high = cv2.getTrackbarPos('V_high', 'Threshold Calibration')
        
        # Create mask
        lower = np.array([h_low, s_low, v_low])
        upper = np.array([h_high, s_high, v_high])
        mask = cv2.inRange(hsv, lower, upper)
        
        # Show original and masked images
        cv2.imshow('Original', frame)
        cv2.imshow('Mask', mask)
        
        # Print current values
        print(f"Lower: [{h_low}, {s_low}, {v_low}], Upper: [{h_high}, {s_high}, {v_high}]")
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Call the function to start calibration
    calibrate_thresholds()
