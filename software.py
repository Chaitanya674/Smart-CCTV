import PIL.Image, PIL.ImageTk
import time
import datetime
import tensorflow as tf
import numpy as np
import webbrowser
import pywhatkit
import threading
import tkinter
import cv2

class MyVideoCapture:
    def __init__(self, video_source=0, width=None, height=None, fps=None, phone=None):
    
        self.video_source = video_source
        self.width = width
        self.height = height
        self.fps = fps
        self.phone = phone
        self.vid = cv2.VideoCapture(video_source)
        #check for variable 
        if not self.vid.isOpened():
            raise ValueError("[MyVideoCapture] Unable to open video source", video_source)
        if not self.width:
            self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))   
        if not self.height:
            self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))  
        if not self.fps:
            self.fps = int(self.vid.get(cv2.CAP_PROP_FPS)) 
       
        self.ret = False
        self.frame = None

        # start Camera visual thread
        self.running = True
        self.thread = threading.Thread(target=self.process)
        #prediction thread
        self.thread_pred = threading.Thread(target=self.predictor)
        self.thread.start()
        self.thread_pred.start()
        
    def predictor(self):
        self.model = tf.keras.models.load_model('model3.h5')
        frames = []
        i = 0
        while self.vid.isOpened and self.running:
            time.sleep(0.5)
            _, frame = self.vid.read()
            resized_frame = cv2.resize(frame , (64, 64))
            normalized_frame= resized_frame / 255
            frames.append(normalized_frame)
            if len(frames) == 20:
                test_features = np.asarray([frames])
                result  = self.model.predict(test_features)
                frames = []
                print(result)
                if result[0][0] <= 0.5 or result[0][1] >= 9.0: 
                    pywhatkit.sendwhatmsg(f"+91{self.phone}" , "Violence detected" , time_hour= datetime.datetime.now().hour,time_min= datetime.datetime.now().minute + 1, tab_close=True)
                    violence_img = PIL.Image.fromarray(frame)
                    violence_img.save(f"Images/frame-{i}.png")
                    time.sleep(60)
                    pywhatkit.sendwhats_image(f"+91{self.phone}", f"./Images/frame-{i}.png" , tab_close=True)
                    i += 1
                    time.sleep(60)

    def process(self):
        while self.running:
            ret, frame = self.vid.read()
            if ret:
                # process image
                frame = cv2.resize(frame, (self.width, self.height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            else:
                print('[MyVideoCapture] stream end:', self.video_source)
                # TODO: reopen stream
                self.running = False
                break
                
            # assign new framet 
            self.ret = ret
            self.frame = frame
            
            # sleep for next frame
            time.sleep(1/self.fps)
    
    def get_frame(self):
        return self.ret, self.frame
    
    def __del__(self):
        # stop thread
        if self.running:
            self.running = False
            self.thread.join()

        # relase stream
        if self.vid.isOpened():
            self.vid.release()
            
class tkCamera(tkinter.Frame):

    def __init__(self, window, text="", video_source=0, width=None, height=None, phone=None):
        super().__init__(window)
        
        self.window = window
        
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source, width, height , phone = phone)

        self.label = tkinter.Label(self, text=text)
        self.label.pack()
        
        self.canvas = tkinter.Canvas(self, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        self.btn_snapshot = tkinter.Button(self, text="Start", command=self.start)
        self.btn_snapshot.pack(anchor='center', side='left')
        
        self.btn_snapshot = tkinter.Button(self, text="Stop", command=self.stop)
        self.btn_snapshot.pack(anchor='center', side='left')
    
        self.btn_snapshot = tkinter.Button(self, text="Snapshot", command=self.snapshot)
        self.btn_snapshot.pack(anchor='center', side='left')
        self.delay = int(1000/self.vid.fps)

        print('[tkCamera] source:', self.video_source)
        print('[tkCamera] fps:', self.vid.fps, 'delay:', self.delay)
        
        self.image = None
        
        self.running = True
        self.update_frame()

    def start(self):
        if not self.running:
            self.running = True
            self.update_frame()

    def stop(self):
        if self.running:
           self.running = False
    
    def snapshot(self):
        if self.image:
            self.image.save(time.strftime("frame-%d-%m-%Y-%H-%M-%S.jpg"))
            
    def update_frame(self):
        ret, frame = self.vid.get_frame()
        
        if ret:
            self.image = PIL.Image.fromarray(frame)
            self.photo = PIL.ImageTk.PhotoImage(image=self.image)
            self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        
        if self.running:
            self.window.after(self.delay, self.update_frame)


class App:

    def __init__(self, window, window_title, video_sources):
        self.window = window
        self.window.title(window_title)
        self.top_bar = tkinter.Frame(self.window ,height=60, width=1440)
        self.top_bar.place(x=0, y=0)
        self.screening_area = tkinter.Frame(main_window)
        self.screening_area.place(y=65, x=0)
        self.vid_sources = video_sources
        self.vids = []
        self.link_var = tkinter.StringVar()
        self.name_var = tkinter.StringVar()
        self.contact_name = tkinter.StringVar()
        self.contact_phone = tkinter.StringVar()
        
        self.Add_vid = tkinter.Button(self.top_bar, text ="+", command = self.Add_vids ,  font=('calibre',30, 'bold'))
        self.Add_vid.place(x=5,y=5 ,height=50, width=50)

        self.contact_person = tkinter.Button(self.top_bar, text="👪",command=self.contact_details,   font=('calibre',30, 'bold'))
        self.contact_person.place(x=60,y=5 ,height=50, width=50)

        self.website = tkinter.Button(self.top_bar, text="🌐",  command=self.webbtn, font=('calibre',30, 'bold'))
        self.website.place(x=115,y=5 ,height=50, width=50)

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    

    def webbtn(self):
        webbrowser.open("www.google.com")
    
    def on_closing(self, event=None):
        print('[App] stoping threads')
        for source in self.vids:
            source.vid.running = False
        print('[App] exit')
        self.window.destroy()

    def submit(self):
        name = self.name_var.get()
        link = self.link_var.get()
        new_vid = (name, int(link))
        self.vid_sources.append(new_vid)
        columns = 3
        self.vids.clear
        for number, source in enumerate(self.vid_sources):
            text, stream = source
            vid = tkCamera(self.screening_area, text, stream, 400, 300, self.contact_phone.get())
            x = number % columns
            y = number // columns
            vid.grid(row=y, column=x)
            self.vids.append(vid)
        self.name_var.set("")
        self.link_var.set("")
        self.add_vid_window.destroy()
    
    def contact_details(self):
        self.contact_window = tkinter.Toplevel(self.window)
        self.contact_window.title("Contact person")
        self.contact_window.geometry("300x100")
        name_label = tkinter.Label(self.contact_window, text = 'Name :', font=('calibre',10, 'bold'))
        name_entry = tkinter.Entry(self.contact_window,textvariable = self.contact_name, font=('calibre',10,'normal'))
        phone_number_label = tkinter.Label(self.contact_window, text = 'Phone :', font = ('calibre',10,'bold'))
        phone_number_entry=tkinter.Entry(self.contact_window, textvariable = self.contact_phone, font = ('calibre',10,'normal'))
        sub_btn=tkinter.Button(self.contact_window,text = 'Change', command = self.contact_details_set)
        name_label.grid(row=0,column=0)
        name_entry.grid(row=0,column=1)
        phone_number_label.grid(row=1,column=0)
        phone_number_entry.grid(row=1,column=1)
        sub_btn.grid(row=2,column=1)

    def contact_details_set(self):
        name = self.contact_name.get()
        phone = self.contact_phone.get()
        self.contact_name.set(name)
        self.contact_phone.set(phone)
        self.contact_window.destroy()
    
    def Add_vids(self):
        self.add_vid_window = tkinter.Toplevel(self.window)
        self.add_vid_window.title("Add Screen")
        self.add_vid_window.geometry("300x100")
        name_label = tkinter.Label(self.add_vid_window, text = 'Name', font=('calibre',10, 'bold'))
        name_entry = tkinter.Entry(self.add_vid_window,textvariable = self.name_var, font=('calibre',10,'normal'))
        link_label = tkinter.Label(self.add_vid_window, text = 'RTSP Link', font = ('calibre',10,'bold'))
        link_entry=tkinter.Entry(self.add_vid_window, textvariable = self.link_var, font = ('calibre',10,'normal'))
        sub_btn=tkinter.Button(self.add_vid_window,text = 'Submit', command = self.submit)
        name_label.grid(row=0,column=0)
        name_entry.grid(row=0,column=1)
        link_label.grid(row=1,column=0)
        link_entry.grid(row=1,column=1)
        sub_btn.grid(row=2,column=1)

if __name__ == '__main__':      
    welcome_widow = tkinter.Tk()
    welcome_widow.title("Loading...")
    welcome_widow.geometry('240x80')

    welcome_label = tkinter.Label(welcome_widow , text="WELCOME TO SMART CCTV")
    welcome_label.pack(pady=20 , anchor="center")
    def task():
        welcome_widow.destroy()

    welcome_widow.after(1000, task)
    welcome_widow.mainloop()

    sources = [
    ] 
    main_window = tkinter.Tk()
    App(main_window, "Smart CCTV", sources)