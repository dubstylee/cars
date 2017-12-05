from shared import mqtt_client, send_message
import time
import sys

NUM_CARS = 4
ON = False

occupied = {"cz1": None, "cz2": None, "cz3": None, "cz4": None}
occupying = {}
empty_counts = []
exit_count = 0

# populate occupying dictionary (car 1 occupying cz1, for example)
for i in range(NUM_CARS + 1):
    occupying[str(i)] = None


def on_message(client, userdata, msg):
    global NUM_CARS
    global ON
    global empty_counts
    global exit_count
    message = msg.payload
    splits = message.split(' ')
    action = splits[3]

    # only care about ENTER, MOVE, EXIT, TAKESTEP
    if action not in ["ENTER", "MOVE", "EXIT", "TAKESTEP", "RESETGUI"]:
        return

    if action == "RESETGUI":
        empty_counts = []
        exit_count = 0
        for cz, car in occupied.iteritems():
            occupied[cz] = None
        for i in range(len(occupying)):
            occupying[str(i)] = None
        ON = False
    elif action == "TAKESTEP":
        if ON:
            check_occupied()
        else:
            ON = True
    elif action == "MOVE":
        car_id = splits[4]
        cz_id = splits[5]

        if cz_id != "ez" and occupied[cz_id] is not None:
            print("That space is already occupied!")
            return

        if cz_id == "ez":
            exit_count = exit_count + 1

        if occupying[car_id] is not None:
            old_cz = occupying[car_id]
            if old_cz in ["cz1", "cz2", "cz3", "cz4"]:
                occupied[old_cz] = None

            if cz_id in ["cz1", "cz2", "cz3", "cz4"]:
                occupied[cz_id] = car_id

            occupying[car_id] = cz_id
        else:
            if cz_id == "ez":
                print("moving to ez from nowhere??")

            occupied[cz_id] = car_id
            occupying[car_id] = cz_id
    elif action == "ENTER":
        car_id = splits[4]
        occupying[car_id] = "qz"
    elif action == "EXIT":
        car_id = splits[4]

        if occupying[car_id] != "ez":
            print("car %d is not in the exit zone" % int(car_id))
        else:
            occupying[car_id] = None


def check_occupied():
    empty = 0

    for cz, car in occupied.iteritems():
        if car is None:
            empty = empty + 1

    if exit_count < NUM_CARS:
        empty_counts.append(empty)

    sum_counts = float(sum(empty_counts))
    len_counts = len(empty_counts)
    print("VACANT %d %f" % (empty, sum_counts / len_counts))
    send_message("VACANT %d %f" % (empty, sum_counts / len_counts))


def main():
    global NUM_CARS
    if len(sys.argv) == 2:
        NUM_CARS = int(sys.argv[1])

    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    while True:
        time.sleep(0.5)


if __name__ == "__main__":
    main()
