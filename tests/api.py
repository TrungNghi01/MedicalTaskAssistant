import picar_4wd as fc

from flask import Flask, request, jsonify

import lineFollower as lf

# Create the Flask app
app = Flask(__name__)
# line_follower = lf.LineFollower()
angles = [-90, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90]  # List of angles
index = 0  # Index to track the current angle

@app.route("/api/work", methods=['GET'])
def work():
    global index
    try:
        line_follower = lf.LineFollower()

        line_follower.move_forward_briefly()
        print("moving forward briefly")

        # # Start the line following process
        line_follower.follow_line(show_camera=False)
        print("following line")

        fc.servo.set_angle(angles[index])
        print("set angle")

        index = (index + 1) % len(angles)
        return jsonify({
            "message": "Line following started",
            "angle": angles[index]
        })
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Finish the test
        print("Finishing work")

    # return {"Hello": "World"}

@app.route("/api/stop", methods=['GET'])
def stop():
    global line_follower

    line_follower.destroy()
    return jsonify({"message": "Line follower destroyed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)