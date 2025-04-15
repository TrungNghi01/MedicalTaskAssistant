import lineFollower as lf
import servo as s
import time
from lineFollower import move_forward_briefly

# Test the line follower functionality
line_follower = lf.LineFollower()
line_follower.follow_line()

# Test the servo functionality
s.rotate_servo()
time.sleep(0.5)
move_forward_briefly()
time.sleep(0.5)
line_follower = lf.LineFollower()