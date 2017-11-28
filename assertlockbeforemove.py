from shared import mqtt_client, mqtt_topic, send_message, exit_program
from enum import Enum
import sys
import time

Fluents = {}
trackczid = None

class FluentStatus(Enum) :
    ON = 1
    OFF = 0

class Fluent() :
    status = FluentStatus.OFF
    identifier = 0

    def __init__(self, param) :
        self.identifier = param

    def checkFluent(self, message) :
        print "Checking Fluent"
        # Add LED stuff here
        if message == "LOCK" :
            status = FluentStatus.ON
        elif messsage == "RELEASE" :
            status = FluentStatus.OFF

def on_message(client, userdata, msg) :
    message = msg.payload
    print message
    split = message.split(" ")
    if split[3] == "LOCK" or split[3] == "RELEASE" :
        czid = split[5]
        if(trackzcid != czid)
            return
        carid = int(split[4])
        fluent = Fluents[carid]
        if fluent != None
            fluent.checkFluent(split[3])
    elif split[3] == "MOVE" :
        czid = split[5]
        if(trackzcid != czid)
            return 
        carid = int(split[4])
        fluent = Fluents[carid]
        if fluent != None and fluent.status != FluentStatus.ON
            send_message("ASSERT FAILURE");

def main() :
    numParams = len(sys.argv)

    if numParams < 3 :
        print "Invalid number of arguments, usage : " \
              "python assertlockbeforemove.py <laneid> <carids> ..."
        exit_program()

    trackczid = "cz%d" %int(sys.argv[1])
    for i in range(2, numParames)
        Fluents[numParams] = Fluent(int(sys.argv[i]))

    send_message("LABELA Assert lock before move for lane %d", trackczid)

    while True :
        time.sleep(1)

if __name__ == "__main__":
    main()
