from enum import Enum
from shared import mqtt_client, mqtt_topic, send_message, exit_program, \
                   LOG_LEVEL, LOG_ACTIONS
import random
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
    auto_pilot = False
    state = Status.MAIN
    current_action = 0
    actions = []
    cz_status = {"cz1": False, "cz2": False, "cz3": False, "cz4": False}

    def __init__(self, id, lane_id, next_id):
        self.id = id
        self.lane_id = lane_id
        self.next_id = next_id

    def process_action(self, action):
        if self.auto_pilot:
            # do any special stuff here
            self.actions.append(action)
        else:
            self.actions.append(action)

    def take_action(self):
        if self.current_action < len(self.actions):
            current_action = self.actions[self.current_action]
            act_split = current_action.split(' ')
            if act_split[0] == "LOCK":
                log("CHECK LOCK STATUS FOR %s" % act_split[2])
                lock_state = self.cz_status[act_split[2]]
                if lock_state:
                    log("%s locked" % act_split[2])
                    return
            elif act_split[0] == "TOKEN":
                log("passing token to %d" % int(act_split[1]))
            elif act_split[0] == "MOVE" and act_split[2] == "ez":
                self.state = Status.PARKED

            send_message(self.actions[self.current_action])
            self.current_action = self.current_action + 1

            # after releasing the lock, go ahead and take the next action
            if act_split[0] in ["RELEASE", "LOCK", "TOKEN"]:
                self.take_action()
            elif act_split[0] == "MOVE" and act_split[1] == "ez":
                self.take_action()

    def pass_token(self, id):
        action = "TOKEN %d" % id
        self.process_action(action)

    def lock(self, block):
        action = "LOCK %d %s" % (self.id, block)
        self.process_action(action)

    def move(self, block):
        action = "MOVE %d %s" % (self.id, block)
        self.process_action(action)

    def release(self, block):
        action = "RELEASE %d %s" % (self.id, block)
        self.process_action(action)

    def straight(self):
        if self.lane_id == 1:
            self.lock("cz1")
            self.lock("cz3")
            self.pass_token(self.next_id)
            self.move("cz1")
            self.move("cz3")
            self.release("cz1")
            self.move("ez")
            self.release("cz3")
        if self.lane_id == 2:
            self.lock("cz2")
            self.lock("cz1")
            self.pass_token(self.next_id)
            self.move("cz2")
            self.move("cz1")
            self.release("cz2")
            self.move("ez")
            self.release("cz1")
        if self.lane_id == 3:
            self.lock("cz4")
            self.lock("cz2")
            self.pass_token(self.next_id)
            self.move("cz4")
            self.move("cz2")
            self.release("cz4")
            self.move("ez")
            self.release("cz2")
        if self.lane_id == 4:
            self.lock("cz3")
            self.lock("cz4")
            self.pass_token(self.next_id)
            self.move("cz3")
            self.move("cz4")
            self.release("cz3")
            self.move("ez")
            self.release("cz4")

    def turn_left(self):
        if self.lane_id == 1:
            self.lock("cz1")
            self.lock("cz3")
            self.lock("cz4")
            self.pass_token(self.next_id)
            self.move("cz1")
            self.move("cz3")
            self.release("cz1")
            self.actions.append("TURNLEFT %d" % self.id)
            self.move("cz4")
            self.release("cz3")
            self.move("ez")
            self.release("cz4")
        elif self.lane_id == 2:
            self.lock("cz2")
            self.lock("cz1")
            self.lock("cz3")
            self.pass_token(self.next_id)
            self.move("cz2")
            self.move("cz1")
            self.release("cz2")
            self.actions.append("TURNLEFT %d" % self.id)
            self.move("cz3")
            self.release("cz1")
            self.move("ez")
            self.release("cz3")
        elif self.lane_id == 3:
            self.lock("cz4")
            self.lock("cz2")
            self.lock("cz1")
            self.pass_token(self.next_id)
            self.move("cz4")
            self.move("cz2")
            self.release("cz4")
            self.actions.append("TURNLEFT %d" % self.id)
            self.move("cz1")
            self.release("cz2")
            self.move("ez")
            self.release("cz1")
        elif self.lane_id == 4:
            self.lock("cz3")
            self.lock("cz4")
            self.lock("cz2")
            self.pass_token(self.next_id)
            self.move("cz3")
            self.move("cz4")
            self.release("cz3")
            self.actions.append("TURNLEFT %d" % self.id)
            self.move("cz2")
            self.release("cz4")
            self.move("ez")
            self.release("cz2")

    def turn_right(self):
        if self.lane_id == 1:
            self.lock("cz1")
            self.pass_token(self.next_id)
            self.move("cz1")
            self.actions.append("TURNRIGHT %d" % self.id)
            self.move("ez")
            self.release("cz1")
        elif self.lane_id == 2:
            self.lock("cz2")
            self.pass_token(self.next_id)
            self.move("cz2")
            self.actions.append("TURNRIGHT %d" % self.id)
            self.move("ez")
            self.release("cz2")
        elif self.lane_id == 3:
            self.lock("cz4")
            self.pass_token(self.next_id)
            self.move("cz4")
            self.actions.append("TURNRIGHT %d" % self.id)
            self.move("ez")
            self.release("cz4")
        elif self.lane_id == 4:
            self.lock("cz3")
            self.pass_token(self.next_id)
            self.move("cz3")
            self.actions.append("TURNRIGHT %d" % self.id)
            self.move("ez")
            self.release("cz3")


car = None


def on_message(client, userdata, msg):
    message = msg.payload
    splits = message.split(' ')
    action = splits[3]

    # ignore gui actions
    if action in ["LABELA", "LABELB", "UPDATEA", "UPDATEB"]:
        return

    if action == "RESETGUI":
        car.actions = []
        car.current_action = 0
        car.state = Status.MAIN
        # reset the car's internal cz lock status
        for cz, state in car.cz_status.iteritems():
            car.cz_status[cz] = False

        if car.id == 1:
            car.pass_token(car.id)
            # print("CUR: %d : %s" % (car.current_action, car.actions))

    elif action == "TAKESTEP":
        if car.auto_pilot is False:
            # if car.id == 1:
            #     print("CUR: %d : %s" % (car.current_action, car.actions))
            car.take_action()

    elif action == "LOCK":
        block = splits[5]
        car.cz_status[block] = True

    elif action == "RELEASE":
        block = splits[5]
        car.cz_status[block] = False

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
            # log("check lane %d for convoy" % car.lane_id)
            car.pass_token(car.next_id)
        elif car.state == Status.QUEUED:
            # print(message)
            # lock our blocks then pass the token
            if random.random() * 100 >= 50:
                # go straight
                log("GOING STRAIGHT")
                car.straight()
            #elif random.random() * 100 >= 50:
            else :
                # turn right
                log("TURNING RIGHT")
                car.turn_right()
            #else:
            #    # turn left
            #    log("TURNING LEFT")
            #    car.turn_left()

            car.state = Status.PASSING
            car.take_action()


def log(message):
    if LOG_LEVEL & LOG_ACTIONS:
        print("[CAR %d]: %s" % (car.id, message))


def main():
    global car
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print "Usage: car <id> <lane_id> <next_id> [auto]"
        exit_program()

    car = Car(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    if len(sys.argv) == 5 and sys.argv[4] == "auto":
        car.auto_pilot = True
    mqtt_client.will_set(mqtt_topic, "__WILL OF CAR %d__" % car.id, 0, False)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    if car.id == 1:
        # car 1 starts with the token
        car.pass_token(car.id)

    while True:
        if car.state == Status.MAIN:
            # 50% chance for car to enter QZ
            # if random.randint(1, 10) <= 5:
            send_message("ENTER %d %d" % (car.id, car.lane_id))
            car.state = Status.QUEUED
        elif car.auto_pilot and car.state == Status.PARKED:
            # 20% chance for car to re-enter QZ again
            if random.randint(1, 10) <= 2:
                send_message("ENTER %d %d" % (car.id, car.lane_id))
                car.state = Status.QUEUED

        if car.auto_pilot:
            car.take_action()

        time.sleep(1)


if __name__ == "__main__":
    main()
