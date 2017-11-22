import Tkinter as tk
from enum import Enum
from shared import mqtt_client, mqtt_topic, exit_program

# Intersection Control System GUI (ICS)

class ICS(tk.Frame):
    labels = []

    lanelookup = {
      1 : (0,1),
      2 : (1,3),
      3 : (3,2),
      4 : (2,0)
    }    

    def __init__(self, master, frame, numLanes) :
        laneNumbering = 1
        numBlocks = numLanes*numLanes
        
        # Indices to figure if the block is a critical section
        czs = [1,2]
        # Indices to figure if the block is a quizing zone
        qzs = [0,3]

        tk.Frame.__init__(self, master)
        master.title("Intersection Control System")

        # Dumb work to assign label texts
        for i in range(numLanes) :
            for j in range(numLanes) :
                label = tk.Label(frame, height=20, width=40);
                label.config(highlightthickness=2, highlightbackground="black", highlightcolor="black")
                if(i in czs and j in czs) :
                    # Figure if the current label is going to be a CZ
                    label.config(text="CZ [%d][%d]" %(i,j))
                elif(i in qzs and j in qzs) :
                    # Figure which lane the current Label belongs to                
                    label.config(text="QZ")
                label.grid(row=i, column=j)
                self.labels.append(label)

        # Lane logic
        for key, value in self.lanelookup.iteritems() :
            actualIndex = value[0]*numLanes + value[1];
            print actualIndex
            photo = tk.PhotoImage(file="orangecar.png")
            self.labels[actualIndex].config(image=photo)
            self.labels[actualIndex].photo = photo

def on_message(client, userdata, msg):
    message = mgs.payload
    print message

ics = None

def main():
    global ics
    root = tk.Tk()
    frame = tk.Frame()
    frame.pack()
    ics = ICS(root, frame, 4)

    mqtt_client.will_set(mqtt_topic, '___Will of GUI___', 0, False)
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    root.mainloop()
    exit_program()

if __name__ == "__main__" :
    main()
