__version__ = "1.5.0"

import cv2
import tkinter
from imutils.video import WebcamVideoStream
from tracker import EyeTracking
import numpy as np
from PIL import ImageTk,Image

def list_ports():
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    """
    is_working = True
    dev_port = 0
    working_ports = []
    available_ports = []
    while is_working:
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            is_working = False
            print("Port %s is not working." %dev_port)
        else:
            # is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            # if is_reading:
            #     print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
            #     working_ports.append(dev_port)
            # else:
            print("Port %s for camera ( %s x %s) is present." %(dev_port,h,w))
            available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports

cam_index = 0

class App(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        self._frame = None
        self.switch_frame(Menu)
        self.title("VisionTracker")
        self.ic = ImageTk.PhotoImage(Image.open("unnamed.png"))
        self.iconphoto(False,self.ic)
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        appwidth = 730
        appheight = 710
        x = (ws/2) - (appwidth/2)
        y = (hs/2) - (appheight/2)
        self.geometry("%dx%d+%d+%d"%(appwidth,appheight,x,y))

    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()

class Menu(tkinter.Frame):
    ac = list_ports()
    def __init__(self,master):
        global cam_index
        tkinter.Frame.__init__(self,master)
        tkinter.Frame.configure(self,bg="#4E8098")
        
        self.canvas = tkinter.Canvas(self, width = 735, height = 480,bg="#4E8098",highlightthickness=0)
        self.menuImg = ImageTk.PhotoImage(Image.open("eye.gif"))
        self.canvas.create_image(20,20,anchor=tkinter.NW,image=self.menuImg)
        self.canvas.pack()

        self.label = tkinter.Label(self, bg="#4E8098",text="VisionTracker", fg="#FCF7F8",font=('Forte', 30, "bold")).pack(side="top", fill="x",pady=(0,20))
        
        tkinter.Label(self, bg="#4E8098",text="Hint: Press 'ESC' to close the camera program.",fg="#FCF7F8", font=('Helvetica', 11)).pack(side="top", fill="x")
        
        
        
        self.variable = tkinter.StringVar(self)
        self.variable.set("Camera Source: "+ str(self.ac[0][0])+" (Default)")
        tkinter.Label(self, bg="#4E8098",text="Please select your camera source", fg="#FCF7F8",font=('Helvetica', 11)).pack(side="top", fill="x", pady=5)
        self.opt = tkinter.OptionMenu(self, self.variable, *self.ac[0])
        self.opt.config(width=35, font=('Helvetica', 12),bg="#154a5d",fg="#FCF7F8",highlightbackground="#4E8098",activebackground ="cyan")
        self.opt.pack()

        self.variable.trace("w",self.callback)
        tkinter.Button(self, text="Start", font=('Helvetica', 14,"bold"),width=15, height=2, bg="#154a5d",fg="#FCF7F8",activebackground ="cyan", command=self.show_hide).pack(anchor=tkinter.CENTER, expand=True,side="left",pady=8)
        tkinter.Button(self, text="Quit", font=('Helvetica', 14,"bold"),width=15, height=2, bg="#154a5d",fg="#FCF7F8",activebackground ="cyan",command=self.close).pack(anchor=tkinter.CENTER, expand=True,side="left",pady=8)
        
    def callback(self,*args):
        global cam_index
        cam_index = self.variable.get()

    def show_hide(self):
        self.master.withdraw()
        VisionTracker()
        self.master.deiconify()
    def close(self):
        self.master.destroy()

# class VT(tkinter.Frame):
#     def __init__(self,master):
#         tkinter.Frame.__init__(self, master)
#         tkinter.Frame.configure(self,bg='blue')
        
#         tkinter.Label(self, text="You have closed the OpenCV Window.", font=('Helvetica', 18, "bold")).pack(side="top", fill="x", pady=5)
#         tkinter.Button(self, text="Go back to Menu",
#                   command=lambda: master.switch_frame(Menu)).pack()
#         VisionTracker()

class VisionTracker():
    def __init__(self):
        global cam_index
        src = int(cam_index)
        # cam_index = 0
        # test_cam = cv2.VideoCapture(0)
        # while test_cam is None or not test_cam.isOpened():
        #     cam_index +=1
        video_cap = WebcamVideoStream(src).start()
        fD = EyeTracking()
        
        display = ""
        #Initiate the program
        while(True):
            img = video_cap.read()
            img = cv2.flip(img,1)
            #img = cv2.imread("test.png")
            fD.refresh(img)
            
            img = fD.annotated_frame()
            
            if fD.is_left():
                display = "Looking left"
                cv2.putText(img,"Gazing left. Hello!",(0,300),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,0),2)
            # elif(fD.is_left() and fD.is_bot()):
            #     cv2.putText(img,"Gazing left bottom. Hello!",(0,400),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,0),2)
            elif fD.is_right():
                display = "Looking right"
                cv2.putText(img,"Gazing right. Hello!",(400,300),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,0),2)
            # elif(fD.is_right() and fD.is_bot()):
            #     cv2.putText(img,"Gazing right bottom. Hello!",(400,400),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,0),2)
            elif fD.is_top():
                display = "Looking top"
            elif fD.is_bot():
                display = "Looking bottom"
                cv2.putText(img,"Gazing at bottom, Hello!",(200,400),cv2.FONT_HERSHEY_TRIPLEX,0.7,(0,0,0),1)
            elif fD.is_center():
                display = "Looking center"

            

            cv2.putText(img,"Blink "+str(fD.tem_total)+" times per minute",(0,60),cv2.FONT_HERSHEY_TRIPLEX,0.6,(0,0,0),1)
            cv2.putText(img,"Blinked:"+str(fD.TOTAL),(0,30),cv2.FONT_HERSHEY_TRIPLEX,0.6,(0,0,0),1)
            cv2.putText(img,display,(200,30),cv2.FONT_HERSHEY_TRIPLEX,0.7,(0,0,0),1)
            cv2.putText(img,"Press 'ESC' to quit ",(0,100),cv2.FONT_HERSHEY_COMPLEX_SMALL,0.7,(0,0,0),1)
            
            img = cv2.resize(img,(1000,700))
            # img = adjust_gamma(resized_img,gamma=1.5)
            cv2.imshow('VisionTracker',img)
            
            if cv2.waitKey(1) == 27:
                print("Program is closed")
                break
        cv2.destroyAllWindows()
        video_cap.stop()
        


app = App()
app.mainloop()





