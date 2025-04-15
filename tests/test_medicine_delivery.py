import picar_4wd as fc
import lineFollower as lf

# Create an instance of the LineFollower class
line_follower = lf.LineFollower()

while True:
    print("Moving forward briefly")
    # Move forward briefly
    line_follower.move_forward_briefly()

    # Start the line following process
    line_follower.follow_line()

    # Test the servo functionality
    user_input = input("Insert 1, 2, 3, or 'q' to quit: ").strip().lower()
    if user_input == '1':  # Rotate to the next angle
        fc.servo.set_angle(-90)
    elif user_input == '2':
        fc.servo.set_angle(0)
    elif user_input == '3':
        fc.servo.set_angle(90)
    elif user_input == 'q':  # Quit the program
        print("Exiting...")
        break
    else:
        print("Invalid input. Please press '1', '2', '3', or 'q'.")


# Finish the test
print("destroying line follower")
line_follower.destroy()
