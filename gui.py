import Tkinter as tk
import signal
import sys
from PIL import Image, ImageTk
from enum import Enum
from shared import mqtt_client, mqtt_topic, exit_program, control_c_handler, send_message

# TODO : Add code to handle multiple cars in a lane

# Intersection Control System GUI (ICS)
signal.signal(signal.SIGINT, control_c_handler)

autopilot = False

class ICS(tk.Frame):
    labels = []

    topFrame = None
    bottomFrame = None

    carGridFrame = None
    currentAction = None

    assertLabel = None
    assertText = None
    assertState = "valid"

    propertyLabel = None
    propertyText  = None
    propertyState = "valid"    

    # For Lanes (initrow, initcolumn, orientation)
    laneinfolookup = {
      1 : (0,1, 180),
      2 : (1,3, 90),
      3 : (3,2, 0),
      4 : (2,0, 270)
    }    

    #Used by the UI to fill the Grid values
    revczlookup = {
      (1,1) : "cz1",
      (1,2) : "cz2",
      (2,1) : "cz3",
      (2,2) : "cz4"
    }

    #For tracking is the entering car is to be placed in the QZ.
    initspotstatus = {}
    carswaiting = {}

    #For storing objects of images to be used by lanes
    imagesForLanes = {}

    #For Car (lane, currentrow, currentrow)
    carLocationLookup = {}
    
    #To track which cars are exiting lanes.
    exitqueue = []

    def cleargui(self) :
        self.topFrame.destroy()
        self.bottomFrame.destroy()
        del self.labels[:]
        del self.exitqueue[:]
        self.carLocationLookup = {}
        self.initspotstatus = {}
        self.carswaiting= {}
        self.initgui(4)

    def initgui(self, numLanes) :
        self.topFrame = tk.Frame()
        self.topFrame.grid(row=1, sticky='NSEW')

        self.bottomFrame = tk.Frame()
        self.bottomFrame.grid(row=2, sticky='NSEW')

        laneNumbering = 1
        numBlocks = numLanes*numLanes
        
        # Indices to figure if the block is a critical section
        czs = [1,2]
        # Indices to figure if the block is a quizing zone
        qzs = [0,3]

        self.carGridFrame = tk.Frame(self.topFrame)
        self.carGridFrame.grid(row=1,column=1, sticky='NSEW')
 
        # Dumb work to assign label texts
        for i in range(numLanes) :
            for j in range(numLanes) :
                label = tk.Label(self.carGridFrame, height=10, width=20, bg="white")
                label.config(highlightthickness=2, 
                             highlightbackground="black", 
                             highlightcolor="black")
                if(i in czs and j in czs) :
                    # Figure if the current label is going to be a CZ
                    label.config(text=self.revczlookup[(i,j)])
                elif(i in qzs and j in qzs) :
                    # Figure which lane the current Label belongs to                
                    label.config(text="QZ")
                label.grid(row=i, column=j, sticky='NSEW')
                self.labels.append(label)

        # Lane logic, init the array with images for lanes.
        # Easy lookup later using the map provided the lane id as the key.
        for key, value in self.laneinfolookup.iteritems() :
            actualIndex = value[0]*numLanes + value[1]
            image = Image.open("orangecar.bmp")
            resized = image.resize((100,100), Image.ANTIALIAS)
            rotated = resized.rotate(value[2]);
            photo = ImageTk.PhotoImage(rotated)            
            self.imagesForLanes[key] = photo

        self.currentAction =  tk.Label(self.carGridFrame, text = "Current Action", 
                                       font="Verdana 12 bold")
        self.currentAction.grid(row=numLanes, columnspan=4)

        assertFrame = tk.Frame(self.topFrame)
        assertFrame.grid(row=1,column=2)
        assertFrame.config(highlightthickness=2, 
                                highlightbackground="black", 
                                highlightcolor="black")
        self.assertLabel = tk.Label(assertFrame, width =80)
        self.assertLabel.config(text="", bg="green")
        self.assertLabel.pack()
        self.assertText = tk.Listbox(assertFrame, height= 39,width=80)
        self.assertText.pack()

        self.bottomFrame.config(highlightthickness=2, 
                                highlightbackground="black", 
                                highlightcolor="black") 
        self.propertyLabel = tk.Label(self.bottomFrame, width=164)
        self.propertyLabel.config(text="", bg="green")
        self.propertyLabel.pack()
        self.propertyText = tk.Listbox(self.bottomFrame, width=164)
        self.propertyText.pack()

        takeStepButton = tk.Button(self.bottomFrame, text="Take Step", command=self.sendTakeStep)
        takeStepButton.pack(side=tk.BOTTOM)

        clearButton = tk.Button(self.bottomFrame, text="Clear GUI", command=self.cleargui)
        clearButton.pack(side=tk.BOTTOM)

    def sendTakeStep(self) :
        global autopilot
        if len(self.exitqueue) == 0 :
            self.currentAction.config(text='')
        else :
            actions = ""
            for carid in self.exitqueue :
                actions = "%s;EXIT %d" %(actions, carid)
                carinfo = self.carLocationLookup.get(carid)
                if carinfo != None :
                    carIndex = carinfo[1]*4 + carinfo[2]
                    self.labels[carIndex].config(image='')
                    del self.carLocationLookup[carid]
            del self.exitqueue[:]
            self.currentAction.config(text=actions)
        if not autopilot :
            send_message("TAKESTEP")

    def __init__(self, master, numLanes) :
        tk.Frame.__init__(self, master)
        master.title("Intersection Control System")
        self.initgui(numLanes)

    def updateAssertLabel(self, text) :
        previousText = self.assertLabel.cget("text")
        newText = previousText + "\n" + text
        self.assertLabel.config(text=newText.strip())

    def updateAssertText(self, text) :
        self.assertText.insert(tk.END, text)
        self.assertText.yview(tk.END)
        if "ASSERT FAILURE" in text:
            self.assertState = "invalid"
            self.assertLabel.config(text="Assert Failed", bg="red")

    def updatePropertyLabel(self, text) :
        self.propertyLabel.config(text=text.strip())

    def updatePropertyText(self, text) :
        self.propertyText.insert(tk.END, text)
        self.propertyText.yview(tk.END)
        if "VIOLATION OF PROPERTY" in text:
            self.propertyState = "invalid"
            self.propertyLabel.config(text="Property Violated", bg="red")

    def takeStep(self, params) :
        numLanes = 4
        # Code to move the cars one step ahead
        split = params.split(" ");
        carid = int (split[0])
        czid = split[1]
        carInfo = self.carLocationLookup.get(carid)
        if carInfo == None :
            return
        laneId = carInfo[0]
        currPos = (carInfo[1], carInfo[2])
        nextPos = None
        if laneId == 1 :
            nextPos = (currPos[0] + 1, currPos[1])
        elif laneId == 2 :
            nextPos = (currPos[0], currPos[1] - 1)
        elif laneId == 3 :
            nextPos = (currPos[0] - 1, currPos[1])
        elif laneId == 4 :
            nextPos = (currPos[0], currPos[1] + 1)
        # Fetch the relevant labels, change images
        prevIndex = currPos[0]*numLanes + currPos[1]
        nextIndex = nextPos[0]*numLanes + nextPos[1]
        photo = self.imagesForLanes[laneId]
        self.labels[prevIndex].config(image='')
        self.labels[nextIndex].config(image=photo)
        newLocation = (laneId, nextPos[0], nextPos[1])
        self.carLocationLookup[carid]=newLocation
        # Keep appending to nextstep, till the 'TakeStep'
        # button is pressed.
        prevstep =  self.currentAction.cget("text")
        nextstep = "%s:MOVE %d %s" %(prevstep, carid, czid)
        self.currentAction.config(text=nextstep)
        # Add a queue for cars exiting the Lanes
        # Clear the queue in the next click of 'TakeStep'
        laneinfo = self.laneinfolookup[laneId]
        if czid == "ez" :
            self.exitqueue.append(carid);
        if laneinfo[0] == currPos[0] and laneinfo[1] == currPos[1] :
            # Case where the car is moving from the init tile.
            waitingcarid = self.carswaiting.get(laneId)
            if waitingcarid != None :
                #print "Waiting :::::::::: %d" %waitingcarid
                del self.carswaiting[laneId]
                # Case for moving
                waitpos = (currPos[0], currPos[1])
                if laneId == 1 :
                    waitpos = (waitpos[0], waitpos[1] - 1)
                elif laneId == 2 :
                    waitpos = (waitpos[0] - 1, waitpos[1])
                elif laneId == 3 :
                    waitpos = (waitpos[0], waitpos[1] + 1)
                elif laneId == 4 :
                    waitpos = (waitpos[0] + 1, waitpos[1])
                #print "Init : %d %d" %(currPos[0], currPos[1])
                #print "Wait : %d %d" %(waitpos[0], waitpos[1])
                photo = self.imagesForLanes[laneId] 
                waitIndex = waitpos[0]*numLanes + waitpos[1]
                self.labels[prevIndex].config(image=photo)
                self.labels[waitIndex].config(image='')
                #print "Prev Index %d" %prevIndex
                #print "Wait Index %d" %waitIndex
                self.carLocationLookup[waitingcarid]=(laneId, currPos[0], currPos[1])
            else :
                # Case for just resetting
                self.initspotstatus[laneId] = True

    def putCarInLane(self, carParams) :
        split = carParams.split(" ")
        carid = int(split[0])
        laneid = int(split[1])
        spotfree = self.initspotstatus.get(laneid)
        laneinfo = self.laneinfolookup[laneid]
        initpos = (laneinfo[0], laneinfo[1]) 
        if spotfree == None or spotfree == True :
            self.initspotstatus[laneid] = False
        elif spotfree == False : 
            self.carswaiting[laneid] = carid
            if laneid == 1 :
                initpos = (initpos[0], initpos[1] - 1)
            elif laneid == 2 :
                initpos = (initpos[0] - 1, initpos[1])
            elif laneid == 3 :
                initpos = (initpos[0], initpos[1] + 1)
            elif laneid == 4 :
                initpos = (initpos[0] + 1, initpos[1])
        actualIndex = initpos[0]*4 + initpos[1]
        photo = self.imagesForLanes[laneid]
        self.labels[actualIndex].config(image=photo)
        self.carLocationLookup[carid] = (laneid, initpos[0], initpos[1])            

    def takeTurn(self, turnmessage, caridstr) :
        carid = int(caridstr)
        carinfo = self.carLocationLookup.get(carid)
        if carinfo == None :
            return
        laneid = carinfo[0];
        actualIndex = carinfo[1]*4 + carinfo[2]
        if turnmessage == "TURNRIGHT" :
            newlane = (laneid%4)+1
            photo = self.imagesForLanes[newlane]
            self.labels[actualIndex].config(image=photo)
            self.carLocationLookup[carid] = (newlane, carinfo[1], carinfo[2]) 
        elif turnmessage == "TURNLEFT" :
            newlane = ((laneid-1)%4)
            if newlane == 0 :
               newlane = 4
            photo = self.imagesForLanes[newlane]
            self.labels[actualIndex].config(image=photo)
            self.carLocationLookup[carid] = (newlane, carinfo[1], carinfo[2])

    def updateWaitingQueue(self, tokenParam) :
        carid = int(tokenParam)
        carinfo = self.carLocationLookup.get(carid)
        if carinfo == None :
          return
        laneid = carinfo[0]
        waitingcarid = self.carswaiting.get(laneid)
        if waitingcarid == None or waitingcarid != carid :
          return
        # How to get the id of the car on which this car is waiting on?
        keys = self.carLocationLookup.keys()
        for key in keys :
            value = self.carLocationLookup[key]
            if key != carid and value[0] == laneid :
                print "swapping because of TOKEN : %d" %(carid)
                # This is the case where we need to swap
                # To swap, you only need to swap the carids
                # in the waiting map and the car lookup map
                swapcarinfo = self.carLocationLookup.get(key)
                print "Swap info %d : (%d, %d, %d)" %(key, swapcarinfo[0], swapcarinfo[1], swapcarinfo[2])
                print "With info %d : (%d, %d, %d)" %(carid, carinfo[0], carinfo[1], carinfo[2]) 
                self.carLocationLookup[key] = carinfo
                self.carLocationLookup[carid] = swapcarinfo
                # This is the car that entered first but has no token
                self.carswaiting[laneid] = key
                break
                
def on_message(client, userdata, msg):
    global autopilot
    message = msg.payload
    # print message
    split = message.split(" ", 4)
    if split[3] == "MOVE" :
        if autopilot :
            ics.sendTakeStep()
        ics.takeStep(split[4])
    elif split[3] == "TURNRIGHT" or split[3] == "TURNLEFT":
        ics.takeTurn(split[3],split[4])
    elif split[3] == "LABELA" :
        ics.updateAssertLabel(split[4])
    elif split[3] == "LABELB" :
        ics.updatePropertyLabel(split[4]);
    elif split[3] == "UPDATEA" and ics.assertState == "valid" :
        ics.updateAssertText(split[4]);
    elif split[3] == "UPDATEB" and ics.propertyState == "valid" :
        ics.updatePropertyText(split[4]);
    elif split[3] == "ENTER" :
        # Case where a new vehicle arrives
        ics.putCarInLane(split[4])
    elif split[3] == "TOKEN" :
        # Check if the waiting car gets the token first.
        # Whichever car gets the token first gets to cut in line.
        ics.updateWaitingQueue(split[4])

ics = None

def main():
    global ics
    global autopilot
    root = tk.Tk()
    ics = ICS(root, 4)

    if(len(sys.argv) > 1) :
        autopilot = True

    mqtt_client.will_set(mqtt_topic, '___Will of GUI___', 0, False)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    root.mainloop()
    exit_program()

if __name__ == "__main__" :
    main()
