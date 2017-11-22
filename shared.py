import time
import socket
import sys
import paho.mqtt.client as paho
import signal
from datetime import datetime as dt


# for leds
ON = 0
OFF = 1


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_addr = str(s.getsockname()[0])
s.close()

broker = 'sansa.cs.uoregon.edu'
mqtt_topic = 'cis650/somethingcool'
mqtt_client = paho.Client()
mqtt_client.connect(broker, '1883')
mqtt_client.subscribe(mqtt_topic)


def exit_program():
    mqtt_client.disconnect()
    mqtt_client.loop_stop()
    sys.exit(0)


def control_c_handler(signum, frame):
    exit_program()


def on_connect(client, userdata, flags, rc):
    print("connected")


def on_disconnect(client, userdata, rc):
    print("disconnected in a normal way")


def on_log(client, userdata, level, buf):
    print("log: {}".format(buf))


def send_message(message):
    timestamp = dt.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')
    mqtt_client.publish(mqtt_topic, "[%s] %s %s" %
                        (timestamp, ip_addr, message))


signal.signal(signal.SIGINT, control_c_handler)

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
