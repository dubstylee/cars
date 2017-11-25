import Tkinter as tk
import signal
from PIL import Image, ImageTk
from enum import Enum
from shared import mqtt_client, mqtt_topic, exit_program, control_c_handler

# Intersection Control System GUI (ICS)
signal.signal(signal.SIGINT, control_c_handler)

class ICS(tk.Frame):
    labels = []
    topFrame = None
    bottomFrame = None
    carGridFrame = None
    assertFrame = None    
    messagesFrame = None    

    lanelookup = {
      1 : (0,1, 180),
      2 : (1,3, 90),
      3 : (3,2, 0),
      4 : (2,0, 270)
    }    

    def __init__(self, master, numLanes) :
        tk.Frame.__init__(self, master)
        master.title("Intersection Control System")
       
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
        for key, value in self.lanelookup.iteritems() :
            actualIndex = value[0]*numLanes + value[1]
            print actualIndex
            image = Image.open("orangecar.bmp")
            resized = image.resize((100,100), Image.ANTIALIAS)
            rotated = resized.rotate(value[2]);
            photo = ImageTk.PhotoImage(rotated)            
            self.labels[actualIndex].config(image=photo)
            self.labels[actualIndex].image = photo

        self.assertFrame = tk.Frame(self.topFrame)
        self.assertFrame.grid(row=1,column=2)
        self.assertFrame.config(highlightthickness=2, 
                                highlightbackground="black", 
                                highlightcolor="black")
        label = tk.Label(self.assertFrame, width =50)
        label.config(text="Asserts Label")
        label.pack()
        listbox = tk.Listbox(self.assertFrame, width=50)
        listbox.pack()

        self.messagesFrame = tk.Frame(self.bottomFrame)
        self.messagesFrame.pack()
        self.messagesFrame.config(highlightthickness=2, 
                                  highlightbackground="black", 
                                  highlightcolor="black") 
        label = tk.Label(self.messagesFrame, width=100)
        label.config(text="Messages Label")
        label.pack()
        listbox = tk.Listbox(self.messagesFrame, width=100)
        listbox.pack()

def on_message(client, userdata, msg):
    message = mgs.payload
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
