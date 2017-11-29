import Tkinter as tk
import signal
from PIL import Image, ImageTk
from enum import Enum
from shared import mqtt_client, mqtt_topic, exit_program, control_c_handler, send_message

# TODO : Add code to handle cars exiting through EZ

# Intersection Control System GUI (ICS)
signal.signal(signal.SIGINT, control_c_handler)

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

    imagesForLanes = {}

    # For Lanes (initrow, initcolumn, orientation)
    laneinfolookup = {
      1 : (0,1, 180),
      2 : (1,3, 90),
      3 : (3,2, 0),
      4 : (2,0, 270)
    }    

    # For Car (lane, currentrow, currentrow)
    carLocationLookup = {}

    # For Move actions, should use as a verification
    # for carLocationLookup after step
    # For CZ {id:(row, column)}
    czlookup = {
      "cz1" : (1,1),
      "cz2" : (1,2),
      "cz3" : (2,1),
      "cz4" : (2,2),
      "ez"  : (-1,-1)
    }
    revczlookup = {
      (1,1) : "cz1",
      (1,2) : "cz2",
      (2,1) : "cz3",
      (2,2) : "cz4"
    }

 
    def cleargui(self) :
        self.topFrame.destroy()
        self.bottomFrame.destroy()
        del self.labels[:]
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
        self.currentAction.config(text='')
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

    def takeStep(self, message) :
        numLanes = 4
        # Code to move the cars one step ahead
        split = message.split(" ");
        carid = int (split[4])
        czid = split[5]
        czNextPos = self.czlookup.get(czid)
        carInfo = self.carLocationLookup.get(carid)
        laneId = carInfo[0]
        currPos = (carInfo[1], carInfo[2])
        print "Expected %d %d " %(czNextPos[0], czNextPos[1])
        print "Current %d %d " %(currPos[0], currPos[1]) 
        nextPos = None
        if laneId == 1 :
            nextPos = (currPos[0] + 1, currPos[1])
        elif laneId == 2 :
            nextPos = (currPos[0], currPos[1] - 1)
        elif laneId == 3 :
            nextPos = (currPos[0] - 1, currPos[1])
        elif laneId == 4 :
            nextPos = (currPos[0], currPos[1] + 1)
        print "Calculated %d %d " %(nextPos[0], nextPos[1]) 
        if czNextPos[0] == nextPos[0] and czNextPos[1] == nextPos[1] :
            # Fetch the relevant labels, change images
            prevIndex = currPos[0]*numLanes + currPos[1]
            nextIndex = nextPos[0]*numLanes + nextPos[1]
            photo = self.imagesForLanes[laneId]
            self.labels[prevIndex].config(image='')
            self.labels[nextIndex].config(image=photo)
            newLocation = (laneId, nextPos[0], nextPos[1])
            self.carLocationLookup[carid]=newLocation
            nextstep = self.revczlookup[nextPos]
            steps = self.currentAction.cget("text")
            steps = steps + ":" + "MOVE %d %s" %(carid, nextstep) 
            self.currentAction.config(text=steps)
             
        elif czNextPos[0] == -1 and czNextPos[1] == -1 :
            prevIndex = currPos[0]*numLanes + currPos[1]
            self.labels[prevIndex].config(image='')
            newLocation = (-1, -1, -1)
            self.carLocationLookup[carid]=newLocation
            steps = self.currentAction.cget("text")
            steps = steps + ":" + "EXIT %d" %carid 
            self.currentAction.config(text=steps)

        else :
            print "Error occured while moving one block"

    def putCarInLane(self, carParams) :
        split = carParams.split(" ")
        carid = int(split[0])
        laneid = int(split[1])
  
        print carid
        print laneid

        laneinfo = self.laneinfolookup[laneid]
        initpos = (laneinfo[0], laneinfo[1])
        actualIndex = initpos[0]*4 + initpos[1]
  
        print actualIndex
       
        photo = self.imagesForLanes[laneid]
        self.labels[actualIndex].config(image=photo)
        self.carLocationLookup[carid] = (laneid, initpos[0], initpos[1]) 

def on_message(client, userdata, msg):
    message = msg.payload
    print message
    split = message.split(" ", 4)
    if split[3] == "MOVE" :
        ics.takeStep(message)
    elif split[3] == "LABELA" :
        ics.updateAssertLabel(split[4])
    elif split[3] == "LABELB" :
        ics.updatePropertyLabel(split[4]);
    elif split[3] == "UPDATEA" and ics.assertState == "valid" :
        ics.updateAssertText(split[4]);
    elif split[3] == "UPDATEB" and ics.propertyState == "valid" :
        ics.updatePropertyText(split[4]);
    elif split[3] == "ENTER" :
        #Case where a new vehicle arrives
        ics.putCarInLane(split[4])

ics = None

def main():
    global ics
    root = tk.Tk()
    ics = ICS(root, 4)

    mqtt_client.will_set(mqtt_topic, '___Will of GUI___', 0, False)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    root.mainloop()
    exit_program()

if __name__ == "__main__" :
    main()
