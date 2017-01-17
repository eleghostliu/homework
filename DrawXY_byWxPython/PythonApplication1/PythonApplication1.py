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
preX = -1
preY = -1

def LoadTPLib():
    # have to load 64bits lib
    try:
        ElanTouchdll = windll.LoadLibrary('libusb.dll')
    except Exception as e:
        ElanTouchdll = None
        print (str(e))

    return ElanTouchdll


# Start a socket server
def MainProcess(refresh_callback):
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
        refresh_callback()
        #scoord = Coord(1,2,3,4,5,6)
        #nRet = g_ElanTouchdll.UB_Readdata(byref(pRecvData), nReadDataLen)
        nRet = g_ElanTouchdll.UB_Readdata(byref(scoord), nReadDataLen)
        #scoord = cast(pRecvData, POINTER(Coord))
        #scoord = Coord()
        #scoord = cast(pRecvData, POINTER(Coord))
       
        
        #print(hex(scoord.length), hex(scoord.ReportID), scoord.state, hex(scoord.x), hex(scoord.y))
        # Debug Information
        '''
        sOutput = "[Receive]"
        for i in pRecvData:
            sOutput += hex(i)
            sOutput += ","
        print (len(pRecvData), sOutput)
        '''
        
class DrawPanel(wx.Frame):
    """Draw a line to a panel."""

    def __init__(self):
        wx.Frame.__init__(self, None, title="Drawing")
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        #self.Bind(wx.EVT_PAINT, self.Paint)
        #self.SetBackgroundColour("WHITE")
        self.Centre()
        self.Show(True)
        self.buffer = wx.EmptyBitmap(1920, 1080)  # draw to this
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.Clear()  # black window otherwise

    def OnPaint(self, event=None):
        global scoord, preX, preY
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        #dc = wx.PaintDC(self)
        #dc.Clear()
        dc.SetPen(wx.Pen(wx.BLACK, 4))
        if (preX != -1):
            dc.DrawLine(preX, preY, scoord.x, scoord.y)#(0, 0, 50, 50)
            #wx.BufferedPaintDC(self, self.buffer)
            print(hex(scoord.length), hex(scoord.ReportID), scoord.state, hex(scoord.x), hex(scoord.y))
        preX = scoord.x
        preY = scoord.y


########################################################
# Main Processure
########################################################

def main():
    #print sys.path
    print ("Application start")

    app = wx.App(False)
    frame = DrawPanel()

    # Start a thread to run socket server
    start_new_thread(MainProcess, (frame.Refresh,))

    frame.Show()
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

    time.sleep(0.5)

    g_ElanTouchdll.UB_Poweroff()
    print ("Application end")
    sys.exit()

if __name__ == '__main__':
    main()