from random import random
import sys
import ConfigParser
import time
import subprocess
import getopt
import threading
import ctypes
import module1
import wx
from thread import *
from ctypes import *

if sys.version[0] == '2': input = raw_input   # 2.X compatible

g_ElanTouchdll = None
ARRAY5 = c_ubyte * 60
class Coord(Structure):
    _fields_ = [("length", c_ushort),
                ("ReportID", c_ubyte),
                ("state", c_ubyte),
                ("x", c_ushort),
                ("y", c_ushort),
                ("Pressure", c_int),
                ("data", ARRAY5)]
scoord = Coord()

def LoadTPLib():
    # have to load 64bits lib
    try:
        ElanTouchdll = windll.LoadLibrary('libusb.dll')
    except Exception as e:
        ElanTouchdll = None
        print (str(e))

    return ElanTouchdll


# Start a socket server
def MainProcess():
    # set global variable
    global g_ElanTouchdll

    g_ElanTouchdll = LoadTPLib()
    if g_ElanTouchdll == None:
        print ('Load library fail...')
        sys.exit()
    
    g_ElanTouchdll.UB_PowerOn()

    time.sleep(0.2)

    nReadDataLen = 64    
    #pRecvData = (c_ubyte * nReadDataLen).from_buffer_copy(bytearray(nReadDataLen))
    pRecvData = Coord()
    nRet = g_ElanTouchdll.UB_Readdata(ctypes.byref(pRecvData), nReadDataLen)
    #print(pRecvData[0:6])
    nReadDataLen = 16
    while True:
        #scoord = Coord(1,2,3,4,5,6)
        #nRet = g_ElanTouchdll.UB_Readdata(byref(pRecvData), nReadDataLen)
        nRet = g_ElanTouchdll.UB_Readdata(byref(scoord), nReadDataLen)
        #scoord = cast(pRecvData, POINTER(Coord))
        #scoord = Coord()
        #scoord = cast(pRecvData, POINTER(Coord))
       
        
        print(hex(scoord.length), hex(scoord.ReportID), scoord.state, hex(scoord.x), hex(scoord.y))
        # Debug Information
        '''
        sOutput = "[Receive]"
        for i in pRecvData:
            sOutput += hex(i)
            sOutput += ","
        print (len(pRecvData), sOutput)
        '''
        
class SimpleDraw(wx.Frame):
    def __init__(self, parent, id, title, size=(640, 480)):
        self.points = []
        wx.Frame.__init__(self, parent, id, title, size)

        self.Bind(wx.EVT_LEFT_DOWN, self.DrawDot)
        self.Bind(wx.EVT_PAINT, self.Paint)

        self.SetBackgroundColour("WHITE")
        self.Centre()
        self.Show(True)
        self.buffer = wx.EmptyBitmap(640, 480)  # draw to this
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.Clear()  # black window otherwise


    def DrawDot(self, event):
        global scoord
        self.points.append(event.GetPosition())
        if len(self.points) == 2:
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            dc.Clear()
            dc.SetPen(wx.Pen("#000000", 10, wx.SOLID))
            x1, y1 = scoord.x #self.points[0]
            x2, y2 = scoord.y #self.points[1]
            dc.DrawLine(x1, y1, x2, y2)
            # reset the list to empty
            self.points = []


    def Paint(self, event):
        wx.BufferedPaintDC(self, self.buffer)


########################################################
# Main Processure
########################################################

def main():
    #print sys.path
    print ("Application start")

    # Start a thread to run socket server
    start_new_thread(MainProcess, ())
    app = wx.App(0)
    SimpleDraw(None, -1, "Paint workflow!")
    app.MainLoop()
    

    #wait the user key 'q' to exit
    #objGetch = module1._Getch()
    reply = input('Enter char:')
    while True:
        #pressedKey = objGetch()
        if reply == 'q' : break
        #print(pressedKey)
        if reply == b'q' or reply == 'q':
            break
        elif reply == b's':
            if g_bSendAll == True:
                g_bSendAll = False
                print ('[PYInfo]Send each packet mode.')
            else:
                g_bSendAll = True
                print ('[PYInfo]Send all packet mode.')

    time.sleep(0.5)

    g_ElanTouchdll.UB_Poweroff()
    print ("Application end")
    sys.exit()

if __name__ == '__main__':
    main()