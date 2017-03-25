#https://cdn-learn.adafruit.com/downloads/pdf/adafruit-ultimate-gps-on-the-raspberry-pi.pdf
#http://www.danmandle.com/blog/getting-gpsd-to-work-with-python/

import random
import time
import os
import csv
import numpy as np

#import gps

import Threads as Thrd

class DataManager():
    isEmulate = True
    isRecording = False
    _dataFile = False
    _trackFile = False
    _gpsSession = False
    _hallSpeedSess = False
    _simSession = False
    
    rwThread = False

    folderDir = "RunData_"+time.strftime("%d%m%y")+'/'
    
    #Calcaulted variabels
    lineCrossTimes = []
    
    emuPosI = 0
    
    @classmethod
    def getTrackData(self, colName = False):
        if DataManager._trackFile is False:
            DataManager._trackFile = np.loadtxt('ALLTrackData.csv', delimiter=',')
            
        #1 - 'Index' -  Index, for usefullness
        #2,3 - 'LongLat' - GPS Long and Lat
        #4,5,6 - 'CartCo' - X, Y and Z in meters, finish line as 0,0
        #7 - 'Dist' - Distance along track (cumulative)
        #8 - 'SectDist' - Distance between point and next
        #9 - 'RadCurve' - Radius of this point and neighbours (in X,Y)
        #10 - 'Grad' - Gradient (Z/Dist)
        #11 - 'AngleVert' - Angle to vertical
        
        if colName is False:
            return DataManager._trackFile
        elif colName == "Index":
            return DataManager._trackFile[:,0]
        elif colName == "LongLat":
            return DataManager._trackFile[:,[1,2]]
        elif colName == "CartCo":
            return DataManager._trackFile[:,[4,5,3]]
        elif colName == "Dist":
            return DataManager._trackFile[:,6]
        elif colName == "SectDist":
            return DataManager._trackFile[:,7]
        elif colName == "RadCurve":
            return DataManager._trackFile[:,8]
        elif colName == "Grad":
            return DataManager._trackFile[:,9]
        elif colName == "AngleVert":
            return DataManager._trackFile[:,10]
    
    @classmethod
    def getSpeed(self):
        if DataManager._hallSpeedSess is False:
            DataManager._hallSpeedSess = Thrd.HallSensors(DataManager.isEmulate)
            DataManager._hallSpeedSess.start()
        
        TotS = 0;
        for i in range(1,3):
            obj = DataManager._hallSpeedSess;
            TotS = TotS + (obj.stamps[i][0] - obj.stamps[i][1])
            
        return 1/((TotS/6)*21) #rev/s
            
    @classmethod
    def getGPSReport(self):
        if DataManager._gpsSession is False:
            #This starts a thread which self connects
            DataManager._gpsSession = Thrd.GpsPoller()
            DataManager._gpsSession.start()
        
        return DataManager._gpsSession.curReport
    
    @classmethod
    def getSim(self):
        if DataManager._simSession is False:
            DataManager._simSession = Thrd.SimThread()
            DataManager._simSession.start()
        
        return DataManager._simSession.simStore
            
    @classmethod
    def getGPSPos(self):
        if DataManager.isEmulate:
            LL = DataManager.getTrackData('LongLat')
 
            self.emuPosI += 4
            if self.emuPosI >= len(LL):
                self.emuPosI = 0
                
            return [LL[self.emuPosI,0], LL[self.emuPosI,1]]

        else:
            report = DataManager.getGPSReport()

            if report is not None:
                if report['class'] == 'TPV' and hasattr(report, "lat"):
                    return [report.lon, report.lat]
                
        return None
    
    @classmethod
    def getPosID(self):
        LongLat = DataManager.getGPSPos()
        TrackLongLat = DataManager.getTrackData('LongLat')
        
        Dif = np.absolute(np.subtract(LongLat, TrackLongLat))
        Tot = np.sum(Dif, axis=1)
        return np.argmin(Tot)
            
    @classmethod
    def getGPSSpeed(self):
        if DataManager.isEmulate:
            return random.random()
        else:
            report = DataManager.getGPSReport()
            #print report
            if report is not None:
                if report['class'] == 'TPV' and hasattr(report, "speed"):
                    #print report.speed
                    return report.speed
        
        return None
            
    @classmethod
    def getFCons(self):
        if DataManager.isEmulate:
            return random.random()
        else:
            return 0
            print("This has not been coded yet")
    
    @classmethod
    def getDataFile(self):
        if DataManager._dataFile is False:
            print("File opened")

            path = os.path.dirname(self.folderDir)
            if not os.path.exists(path):
                os.makedirs(path)
                
            DataManager._dataFile = open(DataManager.folderDir+time.strftime("%H%M%S")+'.log', "w")
            
        return DataManager._dataFile
        
    @classmethod
    def beginLog(self):  
        #Make sure previous one is stopped
        DataManager.stopLog()
        
        DataManager.rwThread = Thrd.RWThread()
        DataManager.isRecording = True
        DataManager.rwThread.start()
        
    @classmethod
    def stopLog(self):
        DataManager.isRecording = False
        if DataManager.rwThread is not False:
            DataManager.rwThread.cancel()

        if DataManager._dataFile is not False:
            DataManager._dataFile.close()
            DataManager._dataFile = False
            print("File closed")
            
    @classmethod
    def swapLog(self):
        if DataManager._dataFile is not False:
            DataManager._dataFile.close()
            DataManager._dataFile = False
            print("File swapped")
    
    def __del__(self):
        DataManager.rwThread.cancel()
        DataManager._gpsSession.cancel()
        DataManager._hallSpeedSess.cancel()
        
        if DataManager._dataFile is not False:
            print("File closed")
            DataManager._dataFile.close()