from shared import exit_program, mqtt_client, mqtt_topic, send_message
import signal
import time

properties = {"LOCK_MOVE_RELEASE1": [["LOCK # cz1",
                                      "car[#].cz1.lock"],
                                     ["MOVE # cz1",
                                      "car[#].move.cz1"],
                                     ["RELEASE # cz1",
                                      "car[#].cz1.release"]],
              "LOCK_MOVE_RELEASE2": [["LOCK # cz2",
                                      "car[#].cz2.lock"],
                                     ["MOVE # cz2",
                                      "car[#].move.cz2"],
                                     ["RELEASE # cz2",
                                      "car[#].cz2.release"]],
              "LOCK_MOVE_RELEASE3": [["LOCK # cz3",
                                      "car[#].cz3.lock"],
                                     ["MOVE # cz3",
                                      "car[#].move.cz3"],
                                     ["RELEASE # cz3",
                                      "car[#].cz3.release"]],
              "LOCK_MOVE_RELEASE4": [["LOCK # cz4",
                                      "car[#].cz4.lock"],
                                     ["MOVE # cz4",
                                      "car[#].move.cz4"],
                                     ["RELEASE # cz4",
                                      "car[#].cz4.release"]]}


class Prop():
    def __init__(self, name, alphabet):
        self.name = name
        self.alphabet = alphabet
        self.status = 0
        self.cur_val = 0

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
property_list.sort(key=lambda property: property.name)


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
    action = splits[3]

    # ignore gui actions
    if action.startswith("LABELA") or \
       action.startswith("LABELB") or \
       action.startswith("UPDATEA") or \
       action.startswith("UPDATEB"):
        return

    if action == "RESETGUI":
        for p in property_list:
            p.status = 0
            p.cur_val = 0
        update_properties()
        return

    print(action)

    found = False
    for p in property_list:
        found_inner = False
        actions = p.alphabet
        tmp_val = 0

        for i in range(len(actions)):
            if actions[i][0] == splits[3]:
                # print("matched action")
                new_action = actions[i][0]
                found_inner = True
                break
            elif "#" in actions[i][0]:
                if p.cur_val != 0:
                    new_action = actions[i][0].replace("#", str(p.cur_val))
                    if new_action == action:
                        # print("matched with substitution")
                        found_inner = True
                        break
                else:
                    actions_split = actions[i][0].split(' ')
                    splits_split = splits[3].split(' ')
                    for j in range(len(actions_split)):
                        if actions_split[j] == "#":
                            tmp_val = int(splits_split[j])
                            break
                        elif actions_split[j] != splits_split[j]:
                            # not a match, break out of inner loop
                            # print("%s != %s" % (action, actions[i][0]))
                            break

                    new_action = actions[i][0].replace("#", str(tmp_val))
                    if new_action == action:
                        # print("setting # = %d for %s" %
                        #       (int(splits_split[j]), actions[i][0]))
                        p.cur_val = tmp_val
                        found_inner = True
                        break

        if found_inner:
            print("found_inner for '%s'" % action)
            found = True
            send_message("UPDATEB %s %s %s: %s" %
                         (splits[0], splits[1], p.name, splits[3]))
            if actions[p.status][0].replace("#", str(p.cur_val)) == splits[3]:
                p.status = (p.status + 1) % len(p.alphabet)
                if p.status == 0:
                    p.cur_val = 0
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

    # print(label_str)
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
