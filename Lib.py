#https://cdn-learn.adafruit.com/downloads/pdf/adafruit-ultimate-gps-on-the-raspberry-pi.pdf
#http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/

import numpy as np

#import RPi.GPIO as GPIO
from Tkinter import *
import tkFont

import DataManager as DM
import time
                
class DashGUI: 
    def __init__(self, master):
        #Setup variables that will be displayed
        #self.lastTime = time.time()
        
        self.GPSSpeed = StringVar()
        self.FCons = StringVar()
        self.splitTimes = [StringVar(),StringVar(),StringVar(),StringVar(),StringVar()]
        
        #Fonts
        sectionTitle = tkFont.Font(family = 'Helvetica', size = 24, weight = 'bold')
        general = tkFont.Font(family = 'Helvetica', size = 20)
        
        """screen is 800x480 """
        self.master = master
        master.title("Hydrone Dash")
        master.geometry("800x480")
        master.configure(background='black')
        
        #Create sections
        self.labelSect = Frame(master, bg='black')
        self.labelSect.grid(row=0, column=1, sticky=N+W)
        self.timesSect = Frame(master, bg='black')
        self.timesSect.grid(row=1, column=1, sticky=N+W)
        self.actSect = Frame(master, bg='black')
        self.actSect.grid(row=2, column=1, sticky=N+W)
        
        #Labels
        Label(self.labelSect, text="Stats", font=sectionTitle, bg='black', fg='white').grid(row=0, sticky=N+W)
        self.labelSpeed = Label(self.labelSect, textvariable=self.GPSSpeed, font=general, bg='black', fg='white')
        self.labelSpeed.grid(row=1)
        self.labelFCons = Label(self.labelSect, textvariable=self.FCons, font=general, bg='black', fg='white')
        self.labelFCons.grid(row=2)

        #Times
        Label(self.timesSect, text="Lap Times", font=sectionTitle, bg='black', fg='white').grid(row=0, sticky=N+W)
        self.splitTimeLabels = range(5)
        for i in range(5):
            self.splitTimeLabels[i] = Label(self.timesSect, textvariable=self.splitTimes[i], font=general, bg='black', fg='white')
            self.splitTimeLabels[i].grid(row=i+1, sticky=N+W)
        
        #Actions
        self.start_button = Button(self.actSect, text="Start Logging", command=DM.DataManager.beginLog)
        self.start_button.grid(row=0, column=0)
        
        self.stop_button = Button(self.actSect, text="Stop Logging", command= DM.DataManager.stopLog)
        self.stop_button.grid(row=0, column=1)

        #self.close_button = Button(master, text="Exit", command= master.quit)
        #self.close_button.pack()
        
        #Speed slider
        self.speedSlide = Scale(master, from_=-3, to=3, length=800, resolution=0.01, borderwidth=0, orient=HORIZONTAL, bg="blue")
        self.speedSlide.grid(row=3, column=0, columnspan=2, sticky=S)
        
        mapPlot = MiniMap(master)
        mapPlot.grid(row=0, column=0, rowspan=3)
        mapPlot.plotMap()
        
        mapPlot.startPosTracking()
        self.update() # starts the update loop
        
    def update(self):
        GPSSpeed = DM.DataManager.getSpeed()
        if GPSSpeed is not None:
            self.GPSSpeed.set("%g" % round(GPSSpeed,3) + " m/s")
        else:
            self.GPSSpeed.set("-")
            
        FCons = DM.DataManager.getFCons()
        if GPSSpeed is not None:
            self.FCons.set("%g" % round(FCons,3) + " L/min?")
        else:
            self.GPSSpeed.set("-")
        
        i = 0
        for Val in DM.DataManager.lineCrossTimes:
            if i > 0 and i < 6:
                split = DM.DataManager.lineCrossTimes[i-1] - Val
                self.splitTimes[i-1].set("%gs" % round(split,3))
            i += 1
        
        posI = DM.DataManager.getPosID()
        simData = DM.DataManager.getSim()
        if simData is not None:
            self.speedSlide.set(simData[posI].VSpeedIn - DM.DataManager.getSpeed())
        
        self.master.update_idletasks()
        
        
        
        #print 1/(time.time()-self.lastTime)
        #self.lastTime = time.time()
        self.master.after(100, self.update)

        
class MiniMap(Canvas):
    def __init__(self,master,*args,**kwargs):
        #http://stackoverflow.com/questions/14389918/inherit-from-tkinter-canvas-calling-super-leads-to-error
        Canvas.__init__(self, master=master, *args, **kwargs)
        
        self.xScale = 1
        self.yScale = 1
        self.xTrans = 0
        self.yTrans = 0
        
        self.posPoint = False
        self.lastSide = None
        self.finLine = False
        
        self.size = 420
        self.margin = 10
        
        self.refreshTime = 100
        
        self.config(width=(self.size + 2*self.margin), height=(self.size + 2*self.margin), background='black', highlightbackground='black')
        
        
    def plotMap(self):
        """Process track (and calabrate)"""
        data = DM.DataManager.getTrackData('LongLat')
        
        #Move the map so all positive from 0
        minInDir = data.min(axis=0)
        
        self.xTrans = minInDir[0] * -1
        self.yTrans = minInDir[1] * -1
        data[:,0] += self.xTrans
        data[:,1] += self.yTrans
        
        
        #Scale the map for screen co-ordinates
        maxInDir = data.max(axis=0)
        scaleInDir = self.size/maxInDir
        
        self.xScale = scaleInDir[0]
        self.yScale = scaleInDir[1]
        data[:,0] *= scaleInDir[0]
        data[:,1] *= scaleInDir[1]
        
        #Flip so map points north
        data[:,1]  = (data[:,1]*-1)+self.size
        
        #Add margins
        data += self.margin
        
        i = 0
        for row in data:
            if i == 0:
                self.create_line((row[0], row[1], data[-1][0], data[-1][1]), fill="white", width=2)
            else:
                self.create_line((row[0], row[1], data[i-1][0], data[i-1][1]), fill="white", width=2)
                
            i = i+1
            
            
        """Process finish line"""
        finData = self.posToPixel(np.loadtxt('FinishCoOrds.csv', delimiter=','))
        self.finLine = finData
        self.create_line((finData[0,0], finData[0,1], finData[1,0], finData[1,1]), fill="red")
        
    def startPosTracking(self):
        gpsLL = DM.DataManager.getGPSPos()
        if gpsLL is not None:    
            LongLat = self.posToPixel(gpsLL)
            Long = LongLat[0,0]
            Lat = LongLat[0,1]
            
            if self.posPoint is False:
                self.posPoint = self.create_rectangle((Long-3, Lat-3, Long+3, Lat+3), fill="red")

            else:
                self.coords(self.posPoint, (Long-3, Lat-3, Long+3, Lat+3))

            #http://stackoverflow.com/questions/22668659/calculate-on-which-side-of-a-line-a-point-is
            x0, y0 = self.finLine[0,0], self.finLine[0,1]
            x1, y1 = self.finLine[1,0], self.finLine[1,1]
            x2, y2 = Long, Lat

            value = ((x1 - x0)*(y2 - y0)) - ((x2 - x0)*(y1 - y0))

            #True is greater than 0, right hand side
            #So false to true for going clockwise
            if self.lastSide is None:
                self.lastSide = (value < 0)
            else:
                if self.lastSide == True and (value < 0):
                    DM.DataManager.lineCrossTimes.insert(0, time.time())

                self.lastSide = (value > 0)
        
        self.master.after(self.refreshTime, self.startPosTracking)
        
    #Convert long and lat data into pixels
    def posToPixel(self, data):
        if isinstance(data, list):
            data = np.asarray([data])
        
        data[:,0] = (data[:,0] + self.xTrans) * self.xScale
        data[:,1] = (data[:,1] + self.yTrans) * self.yScale
        data[:,1]  = (data[:,1]*-1) + self.size
        data += self.margin
        
        return data