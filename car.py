from enum import Enum
from shared import mqtt_client, mqtt_topic, send_message, exit_program
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

    def take_action(self):
        if self.current_action < len(self.actions):
            # if self.state in [Status.MAIN, Status.QUEUED, Status.PASSING]:
            #     log(message)

            current_action = self.actions[self.current_action]
            act_split = current_action.split(' ')
            if act_split[0] == "LOCK":
                log("CHECK LOCK STATUS FOR %s" % act_split[2])
                lock_state = self.cz_status[act_split[2]]
                if lock_state:
                    log("%s locked" % act_split[2])
                    return
            elif act_split[0] == "MOVE" and act_split[2] == "ez":
                self.state = Status.PARKED

            send_message(self.actions[self.current_action])
            self.current_action = self.current_action + 1

            # after releasing the lock, go ahead and take the next action
            if act_split[0] == "RELEASE":
                self.take_action()

    def pass_token(self, id):
        self.actions.append("TOKEN %d" % id)
        # send_message("TOKEN %d" % id)

    def lock(self, block):
        self.actions.append("LOCK %d %s" % (self.id, block))
        # print("[CAR %d]: locking block %s" % (self.id, block))
        # send_message("LOCK %d %s" % (self.id, block))

    def move(self, block):
        self.actions.append("MOVE %d %s" % (self.id, block))
        # print("[CAR %d]: moving to block %s" % (self.id, block))
        # send_message("MOVE %d %s" % (self.id, block))

    def release(self, block):
        self.actions.append("RELEASE %d %s" % (self.id, block))
        # print("[CAR %d]: releasing block %s" % (self.id, block))
        # send_message("RELEASE %d %s" % (self.id, block))

    def straight(self):
        if self.id == 1 or self.id == 5:
            self.lock("cz1")
            self.lock("cz3")
            self.pass_token(self.next_id)
            self.move("cz1")
            self.move("cz3")
            self.release("cz1")
            self.move("ez")
            self.release("cz3")
        if self.id == 2 or self.id == 6:
            self.lock("cz2")
            self.lock("cz1")
            self.pass_token(self.next_id)
            self.move("cz2")
            self.move("cz1")
            self.release("cz2")
            self.move("ez")
            self.release("cz1")
        if self.id == 3 or self.id == 7:
            self.lock("cz4")
            self.lock("cz2")
            self.pass_token(self.next_id)
            self.move("cz4")
            self.move("cz2")
            self.release("cz4")
            self.move("ez")
            self.release("cz2")
        if self.id == 4 or self.id == 8:
            self.lock("cz3")
            self.lock("cz4")
            self.pass_token(self.next_id)
            self.move("cz3")
            self.move("cz4")
            self.release("cz3")
            self.move("ez")
            self.release("cz4")

    def turn_right(self):
        if self.id == 1 or self.id == 5:
            self.lock("cz1")
            self.pass_token(self.next_id)
            self.move("cz1")
            self.move("ez")
            self.release("cz1")
        elif self.id == 2 or self.id == 6:
            self.lock("cz2")
            self.pass_token(self.next_id)
            self.move("cz2")
            self.move("ez")
            self.release("cz2")
        elif self.id == 3 or self.id == 7:
            self.lock("cz4")
            self.pass_token(self.next_id)
            self.move("cz4")
            self.move("ez")
            self.release("cz4")
        elif self.id == 4 or self.id == 8:
            self.lock("cz3")
            self.pass_token(self.next_id)
            self.move("cz3")
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

    if action == "TAKESTEP":
        if car.current_action < len(car.actions):
            if car.state in [Status.MAIN, Status.QUEUED, Status.PASSING]:
                log(message)

            current_action = car.actions[car.current_action]
            act_split = current_action.split(' ')
            if act_split[0] == "LOCK":
                log("CHECK LOCK STATUS FOR %s" % act_split[2])
                lock_state = car.cz_status[act_split[2]]
                if lock_state:
                    log("%s locked" % act_split[2])
                    return
            elif act_split[0] == "MOVE" and act_split[2] == "ez":
                car.state = Status.PARKED

            send_message(car.actions[car.current_action])
            car.current_action = car.current_action + 1

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
            log("passing token to %d" % car.next_id)
            car.pass_token(car.next_id)
        elif car.state == Status.PASSING:
            # we are already in the CZ, check for convoy?
            log("check lane %d for convoy" % car.lane_id)
            car.pass_token(car.next_id)
        elif car.state == Status.QUEUED:
            # print(message)
            # lock our blocks then pass the token
            if random.random() * 100 > 50:
                # go straight
                log("GOING STRAIGHT")
                car.straight()
            else:
                # turn right
                log("TURNING RIGHT")
                car.turn_right()

            car.state = Status.PASSING


def log(message):
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

    # enter QZ after random delay
    # delay = 1 + (random.random() * 8)
    # if car.id == 1:
    #    delay = delay + 5
    # log("delaying %f seconds before entering queue" % delay)
    # time.sleep(delay)
    # car.state = Status.QUEUED

    while True:
        # 10% chance for car to enter QZ
        if car.state == Status.MAIN:
            if random.randint(0, 10) == 10:
                car.state = Status.QUEUED


        if car.auto_pilot and car.state in [Status.QUEUED, Status.PASSING, Status.PARKED]:
            car.take_action()

        time.sleep(1)


if __name__ == "__main__":
    main()
