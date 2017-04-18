import wx
#from random import random
import random
import sys
import ConfigParser
import time
import subprocess
import getopt
import threading
import ctypes
import  wx.lib.newevent
import thread
import os
import struct
from retrying import retry
from thread import *
from ctypes import *

if sys.version[0] == '2': input = raw_input   # 2.X compatible


colours = [
    #"BLACK",
    "BLUE",
    "BLUE VIOLET",
    "BROWN",
    "CYAN",
    "DARK GREY",
    "DARK GREEN",
    "GOLD",
    "GREY",
    "GREEN",
    "MAGENTA",
    "NAVY",
    "PINK",
    "RED",
    "SKY BLUE",
    "VIOLET",
    "YELLOW",
    ]

g_ElanTouchdll = None
ARRAY5 = c_ubyte * 60
'''
class Coord(Structure):
    _fields_ = [("length", c_ushort),
                ("ReportID", c_ubyte),
                ("state", c_ubyte),
                ("x", c_ushort),
                ("x1", c_ushort),
                ("y", c_ushort),
                ("y1", c_ushort),
                ("Pressure", c_int),
                ("data", ARRAY5)]
'''
class Coord(Structure):
    _fields_ = [("ReportID", c_ubyte),
                ("state", c_ubyte),
                ("width", c_ubyte),
                ("height", c_ubyte),
                ("x", c_ushort),
                ("x1", c_ushort),
                ("y", c_ushort),
                ("y1", c_ushort),                
                ("data", ARRAY5)]
scoord = Coord()
preX = -1
preY = -1

array_x = []
array_y = []

# This creates a new Event class and a EVT binder function
MooEvent, EVT_MOO = wx.lib.newevent.NewEvent()

def LoadTPLib():
    # have to load 64bits lib
    try:
        ElanTouchdll = windll.LoadLibrary('libusb-0x7.dll')
    except Exception as e:
        ElanTouchdll = None
        print (str(e))

    return ElanTouchdll


# Start a socket server
def MainProcess(win, *args):
    # set global variable
    global g_ElanTouchdll
    print("MainProcess")
    g_ElanTouchdll = LoadTPLib()
    if g_ElanTouchdll == None:
        print ('Load library fail...')
        sys.exit()

    g_ElanTouchdll.UB_PowerOn.argtypes = None
    g_ElanTouchdll.UB_PowerOn.restype = None
    
    ret = g_ElanTouchdll.UB_PowerOn()
    if (ret == -1):
        sys.exit()
        
    time.sleep(0.2)

    nReadDataLen = 64    
    #pRecvData = (c_ubyte * nReadDataLen).from_buffer_copy(bytearray(nReadDataLen))
    pRecvData = Coord()
    #g_ElanTouchdll.UB_Readdata.argtypes = [ctypes.c_uint8, ctypes.c_ulong]
    g_ElanTouchdll.UB_Readdata.restype = ctypes.c_bool
    nRet = g_ElanTouchdll.UB_Readdata(ctypes.byref(pRecvData), nReadDataLen)
    nReadDataLen = 16
    while True:
        #refresh_callback()
        nRet = g_ElanTouchdll.UB_Readdata(byref(scoord), nReadDataLen)
        if (nRet != 1):
            raise Exception("Blah, UB_Readdata function error")
        #print ("reportID=%x stats=%x, x=%x" % (scoord.ReportID, scoord.state, scoord.x))
        #wx.PostEvent(None, evt)
        wx.PostEvent(win, MooEvent(moo=1))

        
def xy_log_parser(self, directory, filename, *args):
    try:
        fp = open(os.path.join(directory, filename), 'r') 
        print(os.path.join(directory, filename))
    except Exception as e:
        print("open file fail")
        print(str(e))
    else:
        self.SetTitle(os.path.join(directory, filename))
        global array_x, array_y
        
        for line in fp:
            #print(line)
            content = line.strip().split(' ')
            #print(content)
            for i, value in enumerate(content):
                if (value == '[PEN]'):                    
                    #linex = array_x.join([content[6], content[5]]) #Incorrect Usage which gave the AttributeError
                    # merge x
                    linex = "".join([content[6], content[5]])                    
                    array_x.append(linex)
                    
                    # merge y
                    liney = "".join([content[8], content[7]])
                    array_y.append(liney)

        print(array_x)
        print(array_y)
        fp.close        

class SketchWindow(wx.Window):
    def __init__(self, parent, ID):
        wx.Window.__init__(self, parent, ID)
        self.SetBackgroundColour("Black")
        #self.color = "Red"
        #self.color = random.choice(['Red', 'Blue', 'White', 'CYAN', 'GREEN', 'YELLOW', 'LIGHT_GREY'])
        self.color = random.choice(colours)
        #print ("color %s" % self.color)
        self.thickness = 10
        self.pen = wx.Pen(self.color, self.thickness, wx.SOLID)
        self.lines = []
        self.curLine = []
        self.pos = (0, 0)
        self.x = 0
        self.y = 0
        self.playback_count = 0
        self.InitBuffer()
        print("create thread")
        th = threading.Thread(target=MainProcess, args=(self, ))
        th.start()
        time.sleep(0.5)

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        #self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        #self.Bind(EVT_LKey, self.OnLeftKey)
        self.Bind(EVT_MOO, self.TouchMotion)
        #self.Bind(EVT_RKey, self.OnRightKey)
       
        self.Bind(wx.EVT_CHAR_HOOK, self.onKey)
        self.pb_win = xy_playback_window()

    def onKey(self, evt):
        if evt.GetKeyCode() == wx.WXK_RIGHT:
            print "right key down"
            self.playback_count += 1
            num = self.playback_count
            self.pb_win.Process_coordEvent(num)
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            self.TouchdrawMotion(dc,-1)
            
        elif evt.GetKeyCode() == wx.WXK_LEFT:
            print "left key down"
            if (self.playback_count > 0):
                self.playback_count -= 1
            num = self.playback_count
            self.pb_win.Process_coordEvent(num)
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            self.TouchdrawMotion(dc,-1)
        else:
            evt.Skip()

    def InitBuffer(self):
        size = self.GetClientSize()
        print("w=%d, h=%d" % (size.width, size.height))
        self.buffer = wx.EmptyBitmap(size.width, size.height)
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.DrawLines(dc)
        self.reInitBuffer = False

    def GetLinesData(self):
        return self.lines[:]

    def SetLinesData(self, lines):
        self.lines = lines[:]
        self.InitBuffer()
        self.Refresh()

    def OnLeftDown(self, event):
        print "OnLeftDown"
        self.curLine = []
        self.pos = event.GetPositionTuple()
        self.CaptureMouse()

    def OnLeftUp(self, event):
        print "OnLeftUp"
        if self.HasCapture():
            self.lines.append((self.color,
                               self.thickness,
                               self.curLine))
            self.curLine = []
            self.ReleaseMouse()

    def OnMotion(self, event):
        print("OnMotion")
        if event.Dragging() and event.LeftIsDown():        
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            self.drawMotion(dc, event)
        event.Skip()

    def drawMotion(self, dc, event):
        dc.SetPen(self.pen)
        newPos = event.GetPositionTuple()
        coords = self.pos + newPos
        self.curLine.append(coords)
        dc.DrawLine(*coords)
        self.pos = newPos

    def TouchMotion(self, event):
        print("TouchMotion")
        #if event.Dragging():
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        self.TouchdrawMotion(dc, event)
        event.Skip()

    def TouchdrawMotion(self, dc, event):
        global scoord, preX, preY
        dc.SetPen(self.pen)
                                          
        w,h = self.GetClientSizeTuple()
        self.x = (scoord.x * w) / 3392
        self.y = (scoord.y * h) / 2112

        if (scoord.state == 0):
            #Pen up or hover
            print ("Finger up")
            
            while True:
                try:
                    c = random.choice(colours)
                    if c is self.color:
                        raise ValueError
                except ValueError:
                    continue
                break
                                                 
            up_pen = wx.Pen(c, self.thickness, wx.SOLID)
            dc.SetPen(up_pen)
            print ("up color=%s" % self.color)
            dc.DrawLine(preX, preY, self.x, self.y)
            preX = preY = -1
        
        if (preX != -1):
            dc.DrawLine(preX, preY, self.x, self.y)
            print("preX=%d, preY=%d, x=%d, y=%d" % 
                  (preX, preY, self.x, self.y))

        if (scoord.state & 0x3):
            preX = self.x    #scoord.x
            preY = self.y    #scoord.y

    def OnSize(self, event):
        print("OnSize")
        self.reInitBuffer = True

    def OnIdle(self, event):
        if self.reInitBuffer:
            print("OnIdle, reInitBuffer=%d" % self.reInitBuffer)
            self.InitBuffer()
            self.Refresh(False)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)

    def DrawLines(self, dc):
        for colour, thickness, line in self.lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            for coords in line:
                dc.DrawLine(*coords)

    def SetColor(self, color):
        self.color = color
        self.pen = wx.Pen(self.color, self.thickness, wx.SOLID)

    def SetThickness(self, num):
        self.thickness = num
        self.pen = wx.Pen(self.color, self.thickness, wx.SOLID)



class xy_playback_window():
    def __init__(self):        
        self.playback_mode = 1

    def Process_coordEvent(self, num):
        global scoord, array_x, array_y       
        number = int(num)                 
        print array_x[number], array_y[number]
        #scoord.x = struct.unpack("h", array_x[number])
        #scoord.y = struct.unpack("h", array_y[number])
        #print scoord.x, scoord.y
        scoord.x = int(array_x[number], 16)
        scoord.y = int(array_y[number], 16)
        print number, scoord.x, scoord.y



class SketchFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Sketch Frame",
                size=(800,600))
        self.dirname = ''
        #self.playback_mode = 0
        self.sketch = SketchWindow(self, -1)

        # Menu bar
        menuBar = wx.MenuBar()
        menu1 = wx.Menu()
        menuItem1 = menu1.Append(wx.ID_OPEN, "Open", 'Open file')
        menuItem2 = menu1.Append(wx.ID_EXIT, 'Exit', "Exit Application")
        #menu1.AppendSeparator()
        menuBar.Append(menu1, "&File")
        self.Bind(wx.EVT_MENU, self.OnOpen, menuItem1)
        self.Bind(wx.EVT_MENU, self.OnExit, menuItem2)

        self.SetMenuBar(menuBar)
        self.sketch.Bind(wx.EVT_MOTION, self.OnSketchMotion)
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-1, -2, -3])
        

    def OnSketchMotion(self, event):
        self.statusbar.SetStatusText("Pos: %s" %
                str(event.GetPositionTuple()), 0)
        self.statusbar.SetStatusText("Current Pts: %s" %
                len(self.sketch.curLine), 1)
        self.statusbar.SetStatusText("Line Count: %s" %
                len(self.sketch.lines), 2)
        event.Skip()

    def OnOpen(self,e):
        with wx.FileDialog(self, "Choose a file to open", self.dirname,
                           "", "Text files (*.txt)|*.txt", 
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                directory, filename = dlg.GetDirectory(), dlg.GetFilename()

                th = threading.Thread(target=xy_log_parser, args=(self, directory, filename))
                th.start()                
                #th.join()
            dlg.Destroy()
    
    def OnExit(self, event):
        print("OnExit")
        self.Close(True)
        #sys.exit()
    

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = SketchFrame(None)    
    frame.Show(True)    
    app.MainLoop()
