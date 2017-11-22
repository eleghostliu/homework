"""
Demonstrates how to convert mathtext to a wx.Bitmap for display in various
controls on wxPython.
"""

import matplotlib
matplotlib.use("WxAgg")
from numpy import arange, sin, pi, cos, log
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx, wxc
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import numpy as np
import wx
import os
import ctw

from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub
from copy import copy


#import wxmplot

ID_ConstantTraceShow = wx.NewId()

DEF_OFFSET_OF_RX_POWER = 27 #28th row
DEF_OFFSET_OF_TX_POWER = 10 #11th row
DEF_DFT_POWER_TAG = 0x6e
DEF_OFFSET_OF_PRESSURE = 12 #13th row
DEF_INDEX_PRESSURE_POS_TAG = 0x8e

#Global
DELIVERY_ARRAY_BUFFER_Rx = []
DELIVERY_ARRAY_BUFFER_Tx = []


font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo

############################################################
# This is where the "magic" happens.
from matplotlib.mathtext import MathTextParser
mathtext_parser = MathTextParser("Bitmap")


def mathtext_to_wxbitmap(s):
    ftimage, depth = mathtext_parser.parse(s, 150)
    return wxc.BitmapFromBuffer(
        ftimage.get_width(), ftimage.get_height(),
        ftimage.as_rgba_str())
############################################################

functions = [
    (r'$\sin(2 \pi x)$', lambda x: sin(2*pi*x)),
    (r'$\frac{4}{3}\pi x^3$', lambda x: (4.0/3.0)*pi*x**3),
    (r'$\cos(2 \pi x)$', lambda x: cos(2*pi*x)),
    (r'$\log(x)$', lambda x: log(x))
]



class CanvasFrame(wx.Frame):
    def __init__(self, parent, title):
        #wx.Frame.__init__(self, parent, -1, title, size=(550, 350))
        super(CanvasFrame, self).__init__(parent, wx.ID_ANY, title, size=(800, 600))
        self.SetBackgroundColour(wxc.NamedColour("WHITE"))

        

        self.decode = normal_test_mode_decode(0)
        self.chip_num = -1
        self.num_of_rx = -1
        self.num_of_tx = -1
        self.array_type = -1
        self.ic_type = -1
        self.frame_index = -1
        self.prev_dft_tx = 0
        self.prev_dft_rx = 0
        self.tx_max_dft = []
        self.rx_max_dft = []
        self.ctw_tx = -1
        self.ctw_rx = -1
 
        self.figure = Figure()
        self.axes = self.figure.add_subplot(211)
        self.axes2 = self.figure.add_subplot(212)

        self.canvas = FigureCanvas(self, -1, self.figure)
 

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        ##self.add_buttonbar()
        self.add_infobar()

        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.add_toolbar()  # comment this out for no toolbar

        #key event
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeypress)
        
        menuBar = wx.MenuBar()
        # File Menu
        menu = wx.Menu()
        menuItem1 = menu.Append(wx.ID_OPEN, "Open", 'Open file')
        menuItem2 = menu.Append(wx.ID_EXIT, "Exit", "Exit Program")
        menuBar.Append(menu, "&File")
        
        self.Bind(wx.EVT_MENU, self.OnOpen, menuItem1)
        self.Bind(wx.EVT_MENU, self.OnExit, menuItem2)
        
        pub.subscribe(self.DataChanged, "Data CHANGED")

        fmenu = wx.Menu()
        fmenu.Append(ID_ConstantTraceShow, "Constant trace plot")
        menuBar.Append(fmenu, "&Functions")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnConstantTracePlot, id=ID_ConstantTraceShow)
        
        self.SetSizer(self.sizer)
        self.Fit()        
        #self.OnOpen(-1)

    def add_buttonbar(self):
        self.button_bar = wx.Panel(self)
        self.button_bar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.button_bar, 0, wx.LEFT | wx.TOP | wx.GROW)

        for i, (mt, func) in enumerate(functions):
            bm = mathtext_to_wxbitmap(mt)
            button = wx.BitmapButton(self.button_bar, 1000 + i, bm)
            self.button_bar_sizer.Add(button, 1, wx.GROW)
            self.Bind(wx.EVT_BUTTON, self.OnChangePlot, button)

        self.button_bar.SetSizer(self.button_bar_sizer)

    def add_infobar(self):
        self.infoPanel = wx.Panel(self)
        self.sizer.Add(self.infoPanel, 0, wx.LEFT | wx.TOP)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        Label1 = wx.StaticText(self, label=" IC Type:")
        self.Text1 = wx.TextCtrl(self, style=wx.TE_READONLY)
        Label2 = wx.StaticText(self, label=" Rx Number:")
        self.Text2 = wx.TextCtrl(self, style=wx.TE_READONLY)
        Label3 = wx.StaticText(self, label=" Tx Number:")
        self.Text3 = wx.TextCtrl(self, style=wx.TE_READONLY)
        Label4 = wx.StaticText(self, label=" Tx Index/Power:")
        self.Text4 = wx.TextCtrl(self, size=(130, -1), style=wx.TE_READONLY)
        Label5 = wx.StaticText(self, label=" Rx Index/Power:")
        self.Text5 = wx.TextCtrl(self, size=(130, -1), style=wx.TE_READONLY)
        Label6 = wx.StaticText(self, label=" Pressure")
        self.Text6 = wx.TextCtrl(self, size=(50, -1), style=wx.TE_READONLY)

        
        hsizer.Add(Label1)
        hsizer.AddSpacer(10)
        hsizer.Add(self.Text1)
        hsizer.AddSpacer(10)
        hsizer.Add(Label2)
        hsizer.AddSpacer(10)
        hsizer.Add(self.Text2)
        hsizer.AddSpacer(10)
        hsizer.Add(Label3)
        hsizer.AddSpacer(10)
        hsizer.Add(self.Text3)
        hsizer.AddSpacer(10)
        self.sizer.Add(hsizer, 0, wx.LEFT)# | wx.TOP)
        self.sizer.AddSpacer(10)
        hsizer2.Add(Label4)
        hsizer2.AddSpacer(10)
        hsizer2.Add(self.Text4)
        hsizer2.AddSpacer(10)
        hsizer2.Add(Label5)
        hsizer2.AddSpacer(10)
        hsizer2.Add(self.Text5)
        hsizer2.AddSpacer(10)
        hsizer2.Add(Label6)
        hsizer2.AddSpacer(10)
        hsizer2.Add(self.Text6)
        hsizer2.AddSpacer(10)
        self.sizer.Add(hsizer2, 0, wx.LEFT)# | wx.TOP)
        #self.infoPanel.SetSizer(hsizer)

    def info_update(self):
        self.Text1.Clear()
        self.Text2.Clear()
        self.Text3.Clear()
        self.Text4.Clear()
        self.Text5.Clear()
        self.Text6.Clear()

        self.Text1.AppendText(str(self.ic_type))
        self.Text2.AppendText(str(self.num_of_rx))
        self.Text3.AppendText(str(self.num_of_tx))
        try:    #str_dat = ''.join([s_hex_H, s_hex_L])
            content = ','.join([str(self.tx_max_dft[0]), str(self.tx_max_dft[1]), str(self.tx_max_dft[2]), str(self.tx_max_dft[3])])            
            print content
            self.Text4.AppendText(str(content))
            #self.Text4.SetSizer(content)
            content = ','.join([str(self.rx_max_dft[0]), str(self.rx_max_dft[1]), str(self.rx_max_dft[2]), str(self.rx_max_dft[3])])
            print content
            self.Text5.AppendText(str(content))
            #self.Text5.SetSizer(content)
            content = self.decode.get_pressure()
            self.Text6.AppendText(str(content))
        except Exception as e:
            print e
            pass


    def add_toolbar(self):
        """Copied verbatim from embedding_wx2.py"""
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def OnChangePlot(self, event):
        self.change_plot(event.GetId() - 1000)

    def onKeypress(self, event):
        keycode = event.GetKeyCode()
        #print(keycode)
        if keycode == wx.WXK_LEFT:
            print "key left detect"
            retry_cnt = 0
            
            while retry_cnt < 20:
                res = self.decode.prev_frame(0)
                retry_cnt += 1
                if res == True:
                    break
            
            self.decode.delivery_dft_data()
            self.change_plot(0)
        elif keycode == wx.WXK_RIGHT:
            print "key right detect"
            retry_cnt = 0            
            while True:
                res = self.decode.next_frame(0)
                retry_cnt += 1
                if res == True:
                    break                       
            dft_rx, dft_tx = self.decode.delivery_dft_data()
            self.change_plot(0)
        event.Skip()


    def change_plot(self, plot_number):
        #global DELIVERY_ARRAY_BUFFER_Rx, DELIVERY_ARRAY_BUFFER_Tx
        self.frame_index = self.decode.get_frame_index()
        len_rx = len(DELIVERY_ARRAY_BUFFER_Rx)
        len_tx = len(DELIVERY_ARRAY_BUFFER_Tx)
        
        if len_tx > 0:        
            t_tx = arange(len_tx)
            ###s = functions[plot_number][1](t)        
            if int(self.frame_index) % 3 == 0:
                self.axes2.cla()
            
            self.axes2.plot(t_tx,DELIVERY_ARRAY_BUFFER_Tx, 'o-')
            self.axes2.grid(True, linestyle='-.')
            self.axes2.set_xlabel('Tx index')
            self.axes2.set_xlim(0, len_tx-1)
            min_dft = min(DELIVERY_ARRAY_BUFFER_Tx)
            max_dft = max(DELIVERY_ARRAY_BUFFER_Tx)
            if max_dft > self.prev_dft_tx:
                self.prev_dft_tx = max_dft
            self.axes2.set_ylim(top=self.prev_dft_tx+1000)
            max_idx = (DELIVERY_ARRAY_BUFFER_Tx.index(max(DELIVERY_ARRAY_BUFFER_Tx)))
            del self.tx_max_dft[:]
            self.tx_max_dft.append(max_idx)
            self.tx_max_dft.append(DELIVERY_ARRAY_BUFFER_Tx[max_idx-1])
            self.tx_max_dft.append(DELIVERY_ARRAY_BUFFER_Tx[max_idx])
            self.tx_max_dft.append(DELIVERY_ARRAY_BUFFER_Tx[max_idx+1])

        if len_rx > 0:
            t_rx = arange(len_rx)
            if int(self.frame_index) % 3 == 0:
                self.axes.cla()
            
            self.axes.plot(t_rx,DELIVERY_ARRAY_BUFFER_Rx, 'o-')
            #self.axes.plot(t_rx,DELIVERY_ARRAY_BUFFER_Rx)
            self.axes.set_xlabel('Rx index')
            self.axes.grid(True, linestyle='-.')
            self.axes.set_xlim(0, len_rx-1)
            #self.axes.set_ylim(auto=True)
            min_dft = min(DELIVERY_ARRAY_BUFFER_Rx)
            max_dft = max(DELIVERY_ARRAY_BUFFER_Rx)            
            if max_dft > self.prev_dft_rx:                
                self.prev_dft_rx = max_dft
            self.axes.set_ylim(top=self.prev_dft_rx+1000)
            #self.axes.text(2, max_dft-1000, r'an equation: $E=mc^2$', fontsize=15)
            #self.axes.set_ylim(top=12000)
            max_idx = (DELIVERY_ARRAY_BUFFER_Rx.index(max(DELIVERY_ARRAY_BUFFER_Rx)))
            del self.rx_max_dft[:]
            self.rx_max_dft.append(max_idx)
            self.rx_max_dft.append(DELIVERY_ARRAY_BUFFER_Rx[max_idx-1])
            self.rx_max_dft.append(DELIVERY_ARRAY_BUFFER_Rx[max_idx])
            self.rx_max_dft.append(DELIVERY_ARRAY_BUFFER_Rx[max_idx+1])

       
        self.canvas.draw()
        self.info_update()

         #plt.plot(t,DELIVERY_ARRAY_BUFFER)
         #plt.ylim(-100,12000)        
         #plt.show()
        
    def DataChanged(self, message):
        print(message)

    def OnConstantTracePlot(self, id):
        dlg = ctw.TestDialog(self, -1, "Sample Dialog", size=(350, 200),
                         style=wx.DEFAULT_DIALOG_STYLE, total_rx=self.num_of_rx-1, total_tx=self.num_of_tx-1
                         )
        dlg.CenterOnScreen()
       
        # this does not return until the dialog is closed.
        val = dlg.ShowModal()
        
        self.ctw_tx, self.ctw_rx = dlg.get_user_choice()
        print self.ctw_tx, self.ctw_rx

        dlg.Destroy()  


    
    def OnOpen(self,e):
        with wx.FileDialog(self, "Choose a file to open",
                           wildcard="Text files (*.CSV)|*.CSV", 
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                directory, filename = dlg.GetDirectory(), dlg.GetFilename()
                
                #self.decode = normal_test_mode_decode(filename, directory)
                #print(directory, filename)
                
                self.decode.select_open_file(filename, directory)
                self.chip_num, self.num_of_rx, self.num_of_tx, self.array_type, self.ic_type = self.decode.get_csv_format()
                self.info_update()
   

    def OnExit(self, event):
        print(exit)
        self.decode.quit()
        self.Close(True)
        #sys.exit()


class normal_test_mode_decode(CanvasFrame):
    def __init__(self, value=0):
        self.number_of_frame = value
        self.list_of_frmae = []

    def select_open_file(self, csv_fname, csv_dir):
        try:
            self.fp = open(os.path.join(csv_dir, csv_fname), 'r') 
            print(os.path.join(csv_dir, csv_fname))
        except Exception as e:
            print("open file fail")
            print(str(e))
        else:
            pub.sendMessage("Title Changed", str(os.path.join(csv_dir, csv_fname)))
            #fine max T/Rx DFT            
            '''
            self.list_of_frame = self.fp.readlines()
            self.find_max_dft(self.list_of_frame)
            self.fp.seek(0)
            '''
            
        
        '''
        decode [Info] information
        chip_num, Rx_trace_total, Tx_trace_totoal, xx,xx, array_type, Rx_trace_Master, 
        Rx_trace_slave, Tx_trace_Master, Tx_trace_Slave, IC_type, rest should be 0.
        '''
        content = self.fp.readline()
        #self.prevLine = content
        self.text = content.strip().split(',')
        #print(self.text)
            
        #Get chip number
        self.num_of_chip = int (self.extract_from_tag("[Info]",self.text[0]))
        self.num_of_Rx = int(self.text[1])
        self.num_of_Tx = int(self.text[2])
        self.array_type = int(self.text[5])
        self.ic_type = self.text[10]
        self.frame_index = -1
        self.pressure = 0

        # word = 2Bytes
        self.bytes_of_line = self.num_of_Rx * 2
        #self.fp.close

        self.list_of_fpos = []
        self.index_of_list_fpos = 0
        line_num = 0
        for chunk in iter(lambda: self.fp.readline(), ''):
            self.list_of_fpos.append(self.fp.tell())
            print(line_num, self.fp.tell())
            line_num+=1
        #print 'list_of_fpos[0]=%d' % self.list_of_fpos[0]
        self.list_of_fpos.append(-1)
        self.fp.seek(self.list_of_fpos[0])
        #print(self.fp.readline())

    def extract_from_tag(self, tag, line):
        try:
            i = line.index(tag)
            pos = i + len(tag)
            #print(line[pos])
            return line[pos]
        except ValueError:
            return None

    def get_csv_format(self):
        return self.num_of_chip, self.num_of_Rx, self.num_of_Tx, self.array_type, self.ic_type

    def get_frame_index(self):
        return self.frame_index

    def get_pressure(self):
        return self.pressure

    def prev_frame(self, fdata):
        if self.index_of_list_fpos > 0:
            self.index_of_list_fpos -= 1
        print "index_of_list_fpos=%d, list_of_fpos=%d" % (self.index_of_list_fpos,  self.list_of_fpos[self.index_of_list_fpos])
        self.fp.seek(self.list_of_fpos[self.index_of_list_fpos])
        content = self.fp.readline()
        return self.decode(content)
        #print(content)

    def next_frame(self, fdata):
        if self.list_of_fpos[self.index_of_list_fpos + 1] is not -1:
            self.index_of_list_fpos += 1
        print "index_of_list_fpos=%d, list_of_fpos=%d" % (self.index_of_list_fpos,  self.list_of_fpos[self.index_of_list_fpos])        
        self.fp.seek(self.list_of_fpos[self.index_of_list_fpos])
        content = self.fp.readline()
        return self.decode(content)
        #print(content)

    def decode(self, data):
        self.list_of_sign_data = []
        self.list_of_unsign_data = []
        dframe = data.strip().split(',')

        #Byte0 is frame index
        self.frame_index = dframe[0]

        # check valid frame start string
        if dframe[2] != '26':
            print(dframe[2])
            return False
               
        ''' 
        byte1 is timestamp, skip.
        mutual data end string is -32768, self data is -32767
        '''
        N = 2
        while True:
            if dframe[N] == '-32768':
                break
            s_hex_H = '{:02x}'.format(int(dframe[N+1], 10))
            s_hex_L = '{:02x}'.format(int(dframe[N], 10))
            str_dat = ''.join([s_hex_H, s_hex_L])
            int_dat = int(str_dat, 16)
            sign_dat = np.int16(int_dat)
            self.list_of_sign_data.append(sign_dat)
            self.list_of_unsign_data.append(int_dat)
            N = N + 2
        
        self.pressure = self.pick_pressure(self.list_of_unsign_data)

        return self.pick_shadow_DFT_power(self.list_of_unsign_data, len(self.list_of_unsign_data))
        
    def pick_pressure(self, sort_dat):
        pressure_offset = self.num_of_Rx * DEF_OFFSET_OF_PRESSURE
        if sort_dat[pressure_offset] != DEF_INDEX_PRESSURE_POS_TAG:
            return False
        pressure_pos = pressure_offset + 7
        pressure_obstruct_pos = pressure_offset + 8
        print sort_dat[pressure_pos], sort_dat[pressure_obstruct_pos]
        if sort_dat[pressure_pos] <= 0:
            if sort_dat[pressure_obstruct_pos] > 0:
                return sort_dat[pressure_obstruct_pos]
            else: return 0
        else: return sort_dat[pressure_pos]

    def pick_shadow_DFT_power(self, sort_dat, array_size):        
        tx_dft_shadow_pos = self.num_of_Rx * DEF_OFFSET_OF_TX_POWER        
        if sort_dat[tx_dft_shadow_pos] != DEF_DFT_POWER_TAG:
            return False
        self.list_of_tx_dft = []
        start = tx_dft_shadow_pos + 1 #skip 0x6e tag
        stop = start + self.num_of_Tx
        for i, tx_dft_power in enumerate(sort_dat[start:stop]):
            if i >= self.num_of_Tx: break
            self.list_of_tx_dft.append(tx_dft_power)
        global DELIVERY_ARRAY_BUFFER_Tx
        DELIVERY_ARRAY_BUFFER_Tx = copy(self.list_of_tx_dft)

        #print(self.list_of_tx_dft)

        rx_dft_shadow_pos = self.num_of_Rx * DEF_OFFSET_OF_RX_POWER        
        if sort_dat[rx_dft_shadow_pos] != DEF_DFT_POWER_TAG:
            return False
        self.list_of_rx_dft = []
        start = rx_dft_shadow_pos + 1 #skip 0x6e tag
        stop = start + (self.num_of_Rx - 1)
        for i, rx_dft_power in enumerate(sort_dat[start:stop]):
            if i >= self.num_of_Rx: break
            self.list_of_rx_dft.append(rx_dft_power)
        global DELIVERY_ARRAY_BUFFER_Rx
        DELIVERY_ARRAY_BUFFER_Rx = copy(self.list_of_rx_dft)
        return True

        #print(self.list_of_rx_dft)
        '''
        #WXMPLOT test
        x = np.linspace(0.0, 10.0, 53)
        pframe = wxmplot.MultiPlotFrame(rows=2, cols=3, panelsize=(350, 275))
        pframe.plot(x, self.list_of_rx_dft, panel=(0, 0), labelfontsize=6)
        pframe.Show()
        pframe.Raise()
        '''
    def delivery_dft_data(self):
        print("delivery_dft_data")
        global DELIVERY_ARRAY_BUFFER_Rx, DELIVERY_ARRAY_BUFFER_Tx
        return DELIVERY_ARRAY_BUFFER_Rx, DELIVERY_ARRAY_BUFFER_Tx
    
    def find_max_dft(self, dft_list):

        pass
    
    def quit(self):
        print("normal_test_mode_decode quit")
        try:
            self.fp.close
        except Exception as e:
            print e
        



 
class MyApp(wx.App):
    def OnInit(self):
        frame = CanvasFrame(None, "wxPython mathtext demo app")
        #self.decoder = normal_test_mode_decode(self)

        self.SetTopWindow(frame)
        frame.Show(True)
        return True


if __name__ == '__main__':
    app = MyApp()
    app.MainLoop()
