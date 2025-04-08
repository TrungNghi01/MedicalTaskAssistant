import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt


SERVO_PIN = 17
slotAngles = [0, 29, 66, 115, 165, 240]


GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_servo_angle(angle):
    duty = (angle / 18) + 2
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    pwm.ChangeDutyCycle(0)

def on_message(client, userdata, msg):
    command = msg.payload.decode()
    print(f"Recieved Message: {command}")

    if command == "reset":
        set_servo_angle(slotAngles[0])
    elif command.isdigit():
        slot_num = int(command)
        if 1 <= slot_num <= 7:
            set_servo_angle(slotAngles[slot_num])
    if command == "room1": #this was nathans thought on how we can integrate the movement code.

MQTT_BROKER = "localhost"
MQTT_TOPIC = "pill_dispenser1"

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC)

client.loop_forever()

pwm.stop()
GPIO.cleanup()
