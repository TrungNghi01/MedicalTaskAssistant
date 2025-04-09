import cv2
import numpy as np
import paho.mqtt.client as mqtt
import threading
import time

MQTT_BROKER = "127.0.0.1"
MQTT_TOPIC = "pill_dispenser1"

# === Line Following Logic ===
def run_line_following():
    print("[INFO] Line following started (20 seconds max)...")
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Camera read failed.")
            break

# Image Processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

        height, width = thresh.shape
        crop = thresh[int(height * 0.7):height, :]

        contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPRO>
        direction = "NO LINE"

        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                if cx < width // 3:
                    direction = "LEFT"
                elif cx > 2 * width // 3:
                    direction = "RIGHT"
                else:
                    direction = "STRAIGHT"
            else:
                direction = "CENTER LOST"
        else:
            direction = "NO CONTOUR"

        print(f"[DIR] {direction}")
        cv2.imshow("Camera Feed", frame)
        cv2.imshow("Thresholded View", crop)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Manually stopped.")
            break

        if time.time() - start_time > 20:  # auto-stop after 20 seconds
            print("[INFO] Auto timeout reached (20 seconds).")
            break

    cap.release()
    cv2.destroyAllWindows()

# === MQTT Event Handlers ===
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] Connected to broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"[MQTT] Received message: {payload}")

    if payload == "1":
        run_line_following()

# === Main MQTT Setup ===
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)

client.loop_start()  # Non-blocking loop

print("[SYSTEM] Ready. Waiting for MQTT command '1' to start camera...")

# Keep script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[SYSTEM] Exiting...")
    client.loop_stop()
    client.disconnect()
