from enum import Enum
from shared import mqtt_client, mqtt_topic, send_message, exit_program, ON, OFF
import signal
import sys
import time


class Status(Enum):
    MAIN = 0      # starting state
    QUEUED = 1    # waiting in qz
    PASSING = 2   # in conflict zone
    PARKED = 3    # finished


class Car():
    id = 0
    next_id = 0
    lane_id = 0
    state = Status.MAIN

    def __init__(self, id, lane_id, next_id):
        self.id = id
        self.lane_id = lane_id
        self.next_id = next_id

    def pass_token(self, id):
        send_message("TOKEN %d" % id)

    def lock(self, block):
        print("[CAR %d]: locking block %s" % (self.id, block))
        send_message("LOCK %d %s" % (self.id, block))

    def move(self, block):
        print("[CAR %d]: moving to block %s" % (self.id, block))
        send_message("MOVE %d %s" % (self.id, block))

    def release(self, block):
        print("[CAR %d]: releasing block %s" % (self.id, block))
        send_message("RELEASE %d %s" % (self.id, block))


car = None


def on_message(client, userdata, msg):
    message = msg.payload
    splits = message.split(' ')
    action = splits[3]

    # ignore gui actions
    if action in ["LABELA", "LABELB", "UPDATEA", "UPDATEB"]:
        return

    if action == "RELEASE":
        # see if we want the released block
        block = splits[5]

    elif action == "TOKEN":
        car_id = int(splits[4])

        if car_id != car.id:
            # someone else got the token
            return

        if car.state in [Status.MAIN, Status.PARKED]:
            # pass the token along to next car
            car.pass_token(car.next_id)
        elif car.state == Status.PASSING:
            # we are already in the CZ, check for convoy?
            print("check lane %d for convoy" % car.lane_id)
            car.pass_token(car.next_id)
        elif car.state == Status.QUEUED:
            print(message)
            # lock our blocks then pass the token
            car.lock("cz##")


def main():
    global car
    if len(sys.argv) != 4:
        print "Usage: car <id> <lane_id> <next_id>"
        exit_program()

    car = Car(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    mqtt_client.will_set(mqtt_topic, "__WILL OF CAR %d__" % car.id, 0, False)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    # enter QZ after random delay
    car.state = Status.QUEUED

    if car.id == 1:
        # car 1 starts with the token
        car.pass_token(1)

    while True:
        time.sleep(0.5)


if __name__ == "__main__":
    main()
