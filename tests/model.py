#!/usr/bin/env python3
import logging
from flask import Flask, request, jsonify
import threading
import time, sys, os, socket, re, subprocess
import picar_4wd as fc

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("MedicalTaskAssistant")

# Ensure current directory is in the module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import additional modules (servo must be provided in your project)
import servo

# Try to import integrated line follower from line2.py
try:
    from line2 import LineFollower, move_forward_briefly
    logger.info("Successfully imported from integrated_linefollower.py")
    line_follower_available = True
except Exception as e:
    logger.error(f"Warning: Could not import from line follower module: {e}")
    logger.info("Line following functionality will be limited")
    line_follower_available = False

# Create the Flask app
app = Flask(__name__)

# Global state variables and thread references
line_follower_running = False
line_follower_thread = None
medicine_delivery_running = False
medicine_delivery_thread = None
line_follower_instance = None

# Initialize the line follower (if available)
if line_follower_available:
    try:
        logger.info("Initializing line follower on server start...")
        line_follower_instance = LineFollower(auto_fix_camera=True)
        logger.info(f"Line follower initialized, camera_available: {line_follower_instance.camera_available}")
    except Exception as e:
        logger.exception("Error initializing line follower")
        line_follower_instance = None

@app.route('/api/status', methods=['GET'])
def get_status():
    """Return the current status of the robot."""
    camera_status = False
    if line_follower_instance is not None:
        camera_status = line_follower_instance.camera_available
    return jsonify({
        'status': 'online',
        'line_follower_available': line_follower_available,
        'camera_available': camera_status,
        'line_follower_running': line_follower_running,
        'medicine_delivery_running': medicine_delivery_running
    })

@app.route('/api/camera/fix', methods=['POST'])
def fix_camera():
    """Run the camera fix routine."""
    global line_follower_instance
    try:
        if not line_follower_available:
            return jsonify({'success': False, 'message': 'LineFollower class not available'})
        if line_follower_instance is None:
            line_follower_instance = LineFollower(auto_fix_camera=False)
        success = line_follower_instance.fix_camera()
        return jsonify({
            'success': success,
            'message': 'Camera fix complete' if success else 'Camera fix failed',
            'camera_available': line_follower_instance.camera_available
        })
    except Exception as e:
        logger.exception("Error in /api/camera/fix endpoint")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/servo/rotate', methods=['POST'])
def rotate_servo_endpoint():
    """Rotate servo to a specified angle."""
    data = request.json
    angle = data.get('angle', 0)
    try:
        fc.servo.set_angle(angle)
        return jsonify({'success': True, 'angle': angle})
    except Exception as e:
        logger.exception("Error in /api/servo/rotate endpoint")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/servo/sequence', methods=['POST'])
def servo_sequence():
    """Run a sequence of servo movements on a separate thread."""
    try:
        threading.Thread(target=servo.rotate_servo, daemon=True).start()
        return jsonify({'success': True, 'message': 'Servo sequence started'})
    except Exception as e:
        logger.exception("Error in /api/servo/sequence endpoint")
        return jsonify({'success': False, 'error': str(e)})

def run_line_follower():
    """Run the line-following algorithm in a background thread."""
    global line_follower_running, line_follower_instance
    try:
        line_follower_running = True
        if line_follower_instance is None and line_follower_available:
            line_follower_instance = LineFollower(auto_fix_camera=True)
        if line_follower_instance is not None:
            line_follower_instance.follow_line()
        else:
            simple_line_following()
    except Exception as e:
        logger.exception("Error in line following thread")
    finally:
        line_follower_running = False
        fc.stop()

def simple_line_following():
    """Fallback simple movement pattern if the line follower is unavailable."""
    logger.info("Using simple line following pattern")
    try:
        while line_follower_running:
            fc.forward(10)
            time.sleep(1)
            if not line_follower_running:
                break
            fc.turn_left(10)
            time.sleep(0.3)
            if not line_follower_running:
                break
            fc.forward(10)
            time.sleep(1)
            if not line_follower_running:
                break
            fc.turn_right(10)
            time.sleep(0.3)
    except Exception as e:
        logger.exception("Error in simple line following")
    finally:
        fc.stop()

@app.route('/api/line_follower/start', methods=['POST'])
def start_line_follower():
    """Start the line follower process."""
    global line_follower_thread, line_follower_running
    if line_follower_running:
        return jsonify({'success': False, 'message': 'Line follower already running'})
    try:
        line_follower_thread = threading.Thread(target=run_line_follower, daemon=True)
        line_follower_thread.start()
        return jsonify({'success': True, 'message': 'Line follower started'})
    except Exception as e:
        logger.exception("Error starting line follower")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/line_follower/stop', methods=['POST'])
def stop_line_follower():
    """Stop the line follower process."""
    global line_follower_running
    if not line_follower_running:
        return jsonify({'success': False, 'message': 'Line follower not running'})
    try:
        line_follower_running = False
        fc.stop()
        return jsonify({'success': True, 'message': 'Line follower stopping'})
    except Exception as e:
        logger.exception("Error stopping line follower")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/medicine_delivery/start', methods=['POST'])
def start_medicine_delivery():
    """Start the medicine delivery sequence combining line following and servo activation."""
    global medicine_delivery_running, medicine_delivery_thread
    if medicine_delivery_running:
        return jsonify({'success': False, 'message': 'Medicine delivery already in progress'})
    
    def delivery_process():
        global medicine_delivery_running, line_follower_running
        try:
            medicine_delivery_running = True
            if line_follower_available and line_follower_instance is not None:
                line_follower_instance.follow_line(max_frames=100)
            else:
                simple_line_following()
            fc.stop()
            move_forward_briefly()
            servo.rotate_servo()
            fc.stop()
        except Exception as e:
            logger.exception("Error in medicine delivery process")
        finally:
            medicine_delivery_running = False
            line_follower_running = False

    try:
        medicine_delivery_thread = threading.Thread(target=delivery_process, daemon=True)
        medicine_delivery_thread.start()
        return jsonify({'success': True, 'message': 'Medicine delivery started'})
    except Exception as e:
        logger.exception("Error starting medicine delivery")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/medicine_delivery/stop', methods=['POST'])
def stop_medicine_delivery():
    """Stop the ongoing medicine delivery process."""
    global medicine_delivery_running, line_follower_running
    if not medicine_delivery_running:
        return jsonify({'success': False, 'message': 'Medicine delivery not in progress'})
    try:
        medicine_delivery_running = False
        line_follower_running = False
        fc.stop()
        return jsonify({'success': True, 'message': 'Medicine delivery stopping'})
    except Exception as e:
        logger.exception("Error stopping medicine delivery")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/motors/control', methods=['POST'])
def control_motors():
    """Directly control the motors using commands."""
    data = request.json
    command = data.get('command', 'stop')
    speed = data.get('speed', 10)
    try:
        if command == 'forward':
            fc.forward(speed)
        elif command == 'backward':
            fc.backward(speed)
        elif command == 'left':
            fc.turn_left(speed)
        elif command == 'right':
            fc.turn_right(speed)
        elif command == 'stop':
            fc.stop()
        else:
            return jsonify({'success': False, 'message': 'Unknown command'})
        return jsonify({'success': True, 'command': command, 'speed': speed})
    except Exception as e:
        logger.exception("Error in /api/motors/control endpoint")
        return jsonify({'success': False, 'error': str(e)})

def get_ip_address():
    """Determine the Pi's primary IP address for external access."""
    try:
        ifconfig_output = subprocess.check_output(['ifconfig']).decode('utf-8')
        wlan_matches = re.search(r'wlan0.*?inet\s+(\d+\.\d+\.\d+\.\d+)', ifconfig_output, re.DOTALL)
        if wlan_matches:
            return wlan_matches.group(1)
        eth_matches = re.search(r'eth0.*?inet\s+(\d+\.\d+\.\d+\.\d+)', ifconfig_output, re.DOTALL)
        if eth_matches:
            return eth_matches.group(1)
        inet_addresses = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ifconfig_output)
        for address in inet_addresses:
            if not address.startswith('127.'):
                return address
    except Exception as e:
        logger.exception("Ifconfig method failed")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except Exception as e:
        logger.exception("Socket method failed")
    try:
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        if not IP.startswith('127.'):
            return IP
    except Exception as e:
        logger.exception("Hostname method failed")
    return '127.0.0.1'

if __name__ == '__main__':
    ip_address = get_ip_address()
    logger.info("=" * 50)
    logger.info("MedMax Robot API Server Starting")
    logger.info("=" * 50)
    logger.info(f"API available at: http://{ip_address}:5001/api/")
    logger.info(f"Line follower available: {line_follower_available}")
    if line_follower_instance is not None:
        logger.info(f"Camera available: {line_follower_instance.camera_available}")
    logger.info("=" * 50)
    # For production, use a production WSGI server (e.g., Gunicorn or Waitress)
    app.run(host='0.0.0.0', port=5001, debug=True)
