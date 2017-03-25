from threading import Thread
import time
#import RPi.GPIO as GPIO
#GPIO.setmode(GPIO.BCM)

import DataManager as DM
import Simulation as Sim

class RWThread(Thread):
    def __init__(self):
        super(RWThread, self).__init__()
        self.daemon = True
        self.cancelled = False

    def run(self):
        """Overloaded Thread.run, runs the update 
        method once per every 10 milliseconds."""

        dataFile = DM.DataManager.getDataFile()
        while not self.cancelled:
            LongLat = DM.DataManager.getGPSPos()
            simData = DM.DataManager.getSim()
            posI = DM.DataManager.getPosID()
            
            sendAr = [LongLat[0], LongLat[1], DM.DataManager.getSpeed(), DM.DataManager.getFCons(), simData[posI].VSpeedIn]
            
            line = str(time.time())
            for sect in sendAr:
                line += ","+str(sect)
                
            dataFile.write(line + "\n")
            
            time.sleep(0.5)

    def cancel(self):
        """End this timer thread"""
        self.cancelled = True
        
class GpsPoller(Thread):
    def __init__(self):
        super(GpsPoller, self).__init__()
        
        self.error = None
        self.curReport = None
        self.daemon = True
        self.cancelled = False #setting the thread running to true
        
        self.createConnection()
        
        
        
    def createConnection(self):
        try:
            self.gpsd = gps.gps("localhost", "2947")
            self.gpsd.stream(gps.WATCH_ENABLE) #starting the stream of info
            self.error = None
            
        except:
            self.error = 'Unable to connect to GPS'
            #print 'Unable to connect to GPS'

    def run(self):
        while not self.cancelled:
            if self.error == 'Unable to connect to GPS':
                time.sleep(0.1)
                self.createConnection()
                time.sleep(0.1)
            else:
                try:
                    #this will continue to loop and grab EACH set of gpsd info to clear the buffer
                    self.curReport = self.gpsd.next()
                    self.error = None
                    #print "updated"
                    
                except:
                    self.error = 'Fetch error'
                    self.createConnection()
                    #print 'Fetch error'
            
    def cancel(self):
        """End this timer thread"""
        self.cancelled = True
        
class HallSensors(Thread):
    stamps = False;
    emulate = False;
    
    def __init__(self, emulate):
        super(HallSensors, self).__init__()
        
        self.error = None
        self.curReport = None
        self.daemon = True
        self.cancelled = False #setting the thread running to true
        
        self.stamps = {1: [time.time(), time.time()],
                2: [time.time(), time.time()], 
                3: [time.time(), time.time()],
                4: [time.time(), time.time()],
                5: [time.time(), time.time()],
                6: [time.time(), time.time()]}
        
        if not emulate:
            GPIO.setup(17 , GPIO.IN)
            GPIO.setup(18 , GPIO.IN)
            GPIO.setup(19 , GPIO.IN)
        
        self.emulate = emulate
        
    def stateChange(self, state):
        arr = self.stamps[state]
        arr.pop()
        arr.insert(0, time.time())
        self.stamps[state] = arr
        
    def run(self):
        if self.emulate:
            iit = 1;
            while not self.cancelled:
                self.stateChange(iit)
                
                iit = iit + 1
                if iit > 6:
                    iit = 1
                    
                time.sleep(0.1)
                
        else:
            GPIO.add_event_detect(17, GPIO.FALLING, callback=self.stateChange(1))  
            GPIO.add_event_detect(17, GPIO.RISING, callback=self.stateChange(2))
            GPIO.add_event_detect(18, GPIO.FALLING, callback=self.stateChange(3))  
            GPIO.add_event_detect(18, GPIO.RISING, callback=self.stateChange(4))
            GPIO.add_event_detect(19, GPIO.FALLING, callback=self.stateChange(5))  
            GPIO.add_event_detect(19, GPIO.RISING, callback=self.stateChange(6))
            
            
    def cancel(self):
        """End this timer thread"""
        GPIO.cleanup()
        self.cancelled = True
 

class SimThread(Thread):
    def __init__(self):
        super(SimThread, self).__init__()
        
        self.error = None
        self.curPlan = None
        self.daemon = True
        self.cancelled = False #setting the thread running to true
        
        self.simStore = None
        
    def run(self):
        while not self.cancelled:
            #try:
                #this will run the loop as many times as it can
            self.simStore = self.calcPlan()
            self.error = None
            time.sleep(2)

            #except:
            #    self.error = 'Simulation error'
            #    print 'Simulation error'
            
    def cancel(self):
        """End this timer thread"""
        self.cancelled = True
        
    def calcPlan(self):
        TD = Sim.TrackData(DM.DataManager.getTrackData(False))
        CD = Sim.CarData()
        RD = Sim.RaceData()
        RL = Sim.RaceLoop()

        simCache = []
        
        curPos = DM.DataManager.getPosID()
        for i in range(curPos, (curPos + TD.dataLength)):
            RL.i = i
            RL.Position = TD.Distance[i]
            RL = Sim.Throttle(TD, RL, CD, RD)
            RL = Sim.VehicleResp(TD, RL, CD, RD)
            RL = Sim.PowerResp(RL, CD)
            
            simCache.insert(0,RL)
        return simCache