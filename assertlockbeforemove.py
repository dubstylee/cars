from shared import mqtt_client, mqtt_topic, send_message, exit_program
from enum import Enum
import sys
import time

mraaAvail = True

try :
    import mraa
except ImportError:
    mraaAvail = False

Fluents = {}
trackczid = None
assertLED = None

class FluentStatus(Enum) :
    ON = 1
    OFF = 0

class Fluent() :
    status = FluentStatus.OFF
    identifier = 0
    fluentLED = None

    def __init__(self, param) :
        global mraaAvail
        self.identifier = param
        if mraaAvail :
            fluentLED = mraa.Gpio((identifier*2)-1)
            fluentLED.dir(mraa.DIR_OUT)
            fluentLED.write(OFF)

    def checkFluent(self, message) :
        # Add LED stuff here
        if message == "LOCK" :
            self.status = FluentStatus.ON
            if mraaAvail :
                fluentLED.write(ON)
        elif message == "RELEASE" :
            self.status = FluentStatus.OFF
            if mraaAvail :
                fluentLED.write(OFF)

def exit_program() :
    global assertLED
    if mraaAvail :
        assertLED.write(OFF)
        for fluent in Fluents.values() :
            fluent.fluentLED.write(OFF)

def on_message(client, userdata, msg) :
    global trackczid
    global Fluents
    message = msg.payload
    split = message.split(" ")
    if split[3] == "LOCK" or split[3] == "RELEASE" :
        czid = split[5]
        if(trackczid != czid) : 
            return
        carid = int(split[4])
        fluent = Fluents.get(carid, None)
        if fluent != None :
            fluent.checkFluent(split[3])
    elif split[3] == "MOVE" :
        czid = split[5]
        if(trackczid != czid) :
            return 
        carid = int(split[4])
        fluent = Fluents.get(carid, None)
        if fluent != None and fluent.status != FluentStatus.ON :
            send_message("ASSERT FAILURE")

def main() :
    global trackczid
    global Fluents
    global mraaAvail
    global assertLED
    numParams = len(sys.argv)

    if not mraaAvail :
        print "mraa is not available, not operating over LEDs"

    if numParams < 3 :
        print "Invalid number of arguments, usage : " \
              "python assertlockbeforemove.py <laneid> <carids> ..."
        exit_program()

    trackczid = "cz%d" %int(sys.argv[1])
    for i in range(2, numParams) :
        Fluents[int(sys.argv[i])] = Fluent(int(sys.argv[i]))

    mqtt_client.on_message = on_message
    mqtt_client.will_set(mqtt_topic, "Will of Assert\n\n", 0, False)
    mqtt_client.loop_start()

    send_message("LABELA Assert lock before move for lane %s" %trackczid)
    if mraaAvail :
        assertLED = mraa.Gpio(i)
        assertLED.dir(mraa.DIR_OUT)
        led.write(ON)

    while True :
        time.sleep(1)

if __name__ == "__main__":
    main()
