import Tkinter as tk
import signal
from PIL import Image, ImageTk
from enum import Enum
from shared import mqtt_client, mqtt_topic, exit_program, control_c_handler

# TODO : Add code to handle cars exiting
# TODO : Add code to keep the UI steady, it changes in case of cars
#        moving between blocks
# TODO : Add code to properly size the assert and property frames


# Intersection Control System GUI (ICS)
signal.signal(signal.SIGINT, control_c_handler)

class ICS(tk.Frame):
    labels = []

    topFrame = None
    bottomFrame = None

    carGridFrame = None

    assertLabel = None
    assertText = None

    messagesLabel = None
    messagesText  = None    

    imagesForLanes = {}

    # For Lanes (initrow, initcolumn, orientation)
    laneinfolookup = {
      1 : (0,1, 180),
      2 : (1,3, 90),
      3 : (3,2, 0),
      4 : (2,0, 270)
    }    

    # For Car (lane, currentrow, currentrow)
    carLocationLookup = {
      1 : (1, 0, 1),
      2 : (2, 1, 3),
      3 : (3, 3, 2),
      4 : (4, 2, 0)
    }

    # For Move actions, should use as a verification
    # for carLocationLookup after step
    # For CZ {id:(row, column)}
    czlookup = {
      1 : (1,1),
      2 : (1,2),
      3 : (2,1),
      4 : (2,2)
    }

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
                label = tk.Label(self.carGridFrame);
                label.config(highlightthickness=2, 
                             highlightbackground="black", 
                             highlightcolor="black")
                if(i in czs and j in czs) :
                    # Figure if the current label is going to be a CZ
                    label.config(text="CZ [%d][%d]" %(i,j))
                elif(i in qzs and j in qzs) :
                    # Figure which lane the current Label belongs to                
                    label.config(text="QZ")
                label.grid(row=i, column=j, sticky='NSEW')
                self.labels.append(label)

        # Lane logic
        for key, value in self.laneinfolookup.iteritems() :
            actualIndex = value[0]*numLanes + value[1]
            print actualIndex
            image = Image.open("orangecar.bmp")
            resized = image.resize((100,100), Image.ANTIALIAS)
            rotated = resized.rotate(value[2]);
            photo = ImageTk.PhotoImage(rotated)            
            self.labels[actualIndex].config(image=photo)
            #self.labels[actualIndex].image = photo
            self.imagesForLanes[key] = photo

        assertFrame = tk.Frame(self.topFrame)
        assertFrame.grid(row=1,column=2)
        assertFrame.config(highlightthickness=2, 
                                highlightbackground="black", 
                                highlightcolor="black")
        assertLabel = tk.Label(assertFrame, width =50)
        assertLabel.config(text="Asserts Label")
        assertLabel.pack()
        assertText = tk.Listbox(assertFrame, width=50)
        assertText.pack()

        messagesFrame = tk.Frame(self.bottomFrame)
        messagesFrame.pack()
        messagesFrame.config(highlightthickness=2, 
                                  highlightbackground="black", 
                                  highlightcolor="black") 
        self.messagesLabel = tk.Label(messagesFrame, width=100)
        self.messagesLabel.config(text="Messages Label")
        self.messagesLabel.pack()
        self.messagesText = tk.Listbox(messagesFrame, width=100)
        self.messagesText.pack()

    def __init__(self, master, numLanes) :
        tk.Frame.__init__(self, master)
        master.title("Intersection Control System")
        self.initgui(numLanes)

    def updateAssertLabel(self, text):
        previousText = self.assertLabel.cget("text")
        newText = previousText + "\n" + text
        self.assertLabel.config(text=newText)

    def updateAssertText(self, text):
        self.assertText.insert(tk.END, text)
        self.assertText.yview(tk.END)  

    def updateMessagesLabel(self, text):
        previousText = self.messagesLabel.cget("text")
        newText = previousText + "\n" + text
        self.messagesLabel.config(text=newText)

    def updateMessagesText(self, text):
        self.messagesText.insert(tk.END, text)
        self.messagesText.yview(tk.END)  

    def takeStep(self, message) :
        numLanes = 4
        # Code to move the cars one step ahead
        split = message.split(" ");
        carid = int (split[4])
        czid = int (split[5])
        czNextPos = self.czlookup.get(czid)
        carInfo = self.carLocationLookup.get(carid)
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
        if czNextPos[0] == nextPos[0] and czNextPos[1] == nextPos[1] :
            # Fetch the relevant labels, change images
            prevIndex = currPos[0]*numLanes + currPos[1]
            nextIndex = nextPos[0]*numLanes + nextPos[1]
            photo = self.imagesForLanes[laneId]
            self.labels[prevIndex].config(image='')
            self.labels[nextIndex].config(image=photo)
            newLocation = (laneId, nextPos[0], nextPos[1])
            self.carLocationLookup.update(carid=newLocation)
        else :
            print "Error occured while moving one block"    

def on_message(client, userdata, msg):
    message = msg.payload
    split = message.split(" ")
    if split[3] == "MOVE" :
        ics.takeStep(message)
    print message

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
