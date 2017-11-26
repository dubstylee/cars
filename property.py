from shared import exit_program, mqtt_client, mqtt_topic, send_message
import signal
import time

properties = {"LOCK_MOVE_RELEASE": [["LOCK <car_id> cz1",
                                     "car[car_id].cz1.lock"],
                                    ["MOVE <car_id> cz1",
                                     "car[car_id].move.cz1"],
                                    ["RELEASE <car_id> cz1",
                                     "car[car_id].cz1.release"]]}


class Prop():
    def __init__(self, name, alphabet):
        self.name = name
        self.alphabet = alphabet
        self.status = 0

    def __repr__(self):
        text = "property %s = (" % self.name
        for i in range(0, len(self.alphabet)):
            action = self.alphabet[i]
            if i == self.status:
                text = text + "[%s] -> " % action[1].upper()
            else:
                text = text + "%s -> " % action[1]
        text = text + "%s)" % self.name
        return text


property_list = []
for p in properties:
    prop = Prop(p, properties[p])
    property_list.append(prop)


def control_c_handler(signum, frame):
    for p in property_list:
        actions = p.alphabet
        if "<>" in actions[p.status][1]:
            send_message("UPDATEB VIOLATION OF PROPERTY %s" % p.name)
        else:
            send_message("UPDATEB %s EXITING GRACEFULLY" % p.name)
    exit_program()


signal.signal(signal.SIGINT, control_c_handler)


def on_message(client, userdata, msg):
    splits = msg.payload.split(' ', 3)

    for p in property_list:
        found = False
        actions = p.alphabet
        for i in range(0, len(actions)):
            if actions[i][0] == splits[3]:
                found = True
                break

        if found:
            send_message("UPDATEB %s %s %s: %s" %
                         (splits[0], splits[1], p.name, splits[3]))
            if actions[p.status][0] == splits[3]:
                p.status = (p.status + 1) % len(p.alphabet)
            elif "<>" in actions[p.status][1]:
                print("ALPHABET ACTION SEEN, STILL WAITING FOR EVENTUALLY")
            else:
                send_message("UPDATEB VIOLATION OF PROPERTY %s" % p.name)

    if found:
        update_properties()


def update_properties():
    label_str = ""

    for i in range(0, len(property_list)):
        if i != 0:
            label_str = label_str + "\n"
        label_str = label_str + ("%s" % property_list[i])

    send_message("LABELB %s" % label_str)


def main():
    mqtt_client.will_set(mqtt_topic, "___Will of SAFETY PROPERTY___", 0, False)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    update_properties()

    while True:
        time.sleep(1.0)

    exit_program()


if __name__ == "__main__":
    main()
