import lineFollower as lf
import servo as s

# Test the line follower functionality
line_follower = lf.LineFollower()
line_follower.follow_line()

# Test the servo functionality
s.rotate_servo()