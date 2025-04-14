import picar_4wd as fc
import time

def rotate_servo():
    try:
        # angles = [-90, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90]  # List of angles

        angles = [0, 29, 66, 115, 165, 240]
        index = 0  # Index to track the current angle

        while True:
            angle = angles[index]  # Set the current angle
            print(f'Angle: {angle}')
            index = (index + 1) % len(angles)  # Move to the next angle, loop back to 0
            fc.servo.set_angle(angle)
            time.sleep(1) # Wait for 1 second before the next measurement
    finally:
        time.sleep(0.2)
        print("exit")

def rotate_servo_by_keyboard():
    try:
        angles = [-89, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90]  # List of angles
        index = 0  # Index to track the current angle

        while True:
            angle = angles[index]  # Set the current angle
            print(f'Angle: {angle}')
            fc.servo.set_angle(angle)

            # Prompt user for input to change the angle
            user_input = input("Press 'r' to rotate right, 'l' to rotate left, or 'q' to quit: ").strip().lower()
            if user_input == 'r':  # Rotate to the next angle
                index = (index + 1) % len(angles)
            elif user_input == 'l':  # Rotate to the previous angle
                index = (index - 1) % len(angles)
            elif user_input == 'q':  # Quit the program
                print("Exiting...")
                break
            else:
                print("Invalid input. Please press 'r', 'l', or 'q'.")
    finally:
        time.sleep(0.2)
        print("exit")


if __name__ == "__main__":
    rotate_servo_by_keyboard()
