from shared import mqtt_client, mqtt_topic, exit_program, send_message, ON, OFF
from enum import Enum
import signal
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
fluentLED = None

def control_c_handler(signum, frame) :
    global assertLED
    global fluentLED 
    print "exiting program"
    if mraaAvail :
        assertLED.write(OFF)
        fluentLED.write(OFF)
    exit_program()

signal.signal(signal.SIGINT, control_c_handler)

class FluentStatus(Enum) :
    ON = 1
    OFF = 0

class Fluent() :
    status = FluentStatus.OFF
    identifier = 0

    def __init__(self, param) :
        self.identifier = param

    def checkFluent(self, message) :
        global fuentLED
        if message == "LOCK" :
            self.status = FluentStatus.ON
        elif message == "RELEASE" :
            self.status = FluentStatus.OFF

def on_message(client, userdata, msg) :
    global trackczid
    global Fluents
    global fluentLED
    global assertLED
    message = msg.payload
    split = message.split(" ")
    if split[3] not in ["LOCK", "RELEASE", "MOVE"] :
        return
    carid = int(split[4])
    czid = split[5]
    if(trackczid != czid) : 
        return 
    if split[3] == "LOCK" or split[3] == "RELEASE" :
        fluent = Fluents.get(carid, None)
        if fluent != None :
            send_message("UPDATEA %s", message) 
            fluent.checkFluent(split[3])
    elif split[3] == "MOVE" :
        fluent = Fluents.get(carid, None)
        if fluent != None :
            send_message("UPDATEA %s", message)
            if fluent.status != FluentStatus.ON :
                send_message("ASSERT FAILURE")
                assertLED.write(OFF)
                fluentLED.write(OFF)
                exit_program()

    if mraaAvail :
        fluentLED.write(OFF)
    for key, value in Fluents.iteritems() :
        if value.status == FluentStatus.ON :
            print "LED for %s" %trackczid
            if mraaAvail :
                fluentLED.write(ON)
            break

def main() :
    global trackczid
    global Fluents
    global mraaAvail
    global assertLED
    global fluentLED
    numParams = len(sys.argv)

    if not mraaAvail :
        print "mraa is not available, not operating over LEDs"

    if numParams < 3 :
        print "Invalid number of arguments, usage : " \
              "python assertlockbeforemove.py <laneid> <carids> ..."
        exit_program()

    czid = int(sys.argv[1])
    trackczid = "cz%d" %czid
 
    for i in range(2, numParams) :
        Fluents[int(sys.argv[i])] = Fluent(int(sys.argv[i]))

    mqtt_client.on_message = on_message
    mqtt_client.will_set(mqtt_topic, "Will of Assert\n\n", 0, False)
    mqtt_client.loop_start()

    #The trailing 2 is added because the LEDs are indexed from 2 to 9
    assertLEDid = (czid - 1)*2
    fluentLEDid = (assertLEDid + 1)
    print "Assert LED : %d %d" %(assertLEDid, fluentLEDid)
    send_message("LABELA Assert lock before move for lane %s" %trackczid)
    if mraaAvail :
        assertLED = mraa.Gpio(assertLEDid + 2)
        assertLED.dir(mraa.DIR_OUT)
        assertLED.write(ON)
        fluentLED = mraa.Gpio(fluentLEDid + 2)
        fluentLED.dir(mraa.DIR_OUT)
        fluentLED.write(OFF)

    while True :
        time.sleep(1)

if __name__ == "__main__":
    main()
