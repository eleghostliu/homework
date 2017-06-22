import matplotlib.pyplot as plt
import numpy as np

import matplotlib.cbook as cbook
import itertools


SANKE_P1 = r'D:\ELAN_Data\TouchPad\Dell\Starload\tp_pattern_tunning\Log\把计_弊絬\full3mil.txt'
w_SANKE_P1 = r'D:\ELAN_Data\TouchPad\Dell\Starload\tp_pattern_tunning\Log\把计_弊絬\full3mil_w.txt'
w2_SANKE_P1 = r'D:\ELAN_Data\TouchPad\Dell\Starload\tp_pattern_tunning\Log\把计_弊絬\full3mil_w2.txt'
w3_SANKE_P1 = r'D:\ELAN_Data\TouchPad\Dell\Starload\tp_pattern_tunning\Log\把计_弊絬\full3mil_w3.txt'
w_fp = -1
w2_fp = -1
w3_fp = -1


# DFT power parser, log from debug_Linearity.
# report format : 0x17, 0, Rx_DFT_Left(2Word, Low High), Rx_DFT_Medium, RX_DFT_Right, Deviation_Rx, Rx index, 00, 00, 00, 00,
#                          Tx_DFT_Left, Tx_DFT_Medium, Tx_DFT_Right, Deviation_Tx, Tx index
def DFT_Power_Parser():
    try:
        fp = open(SANKE_P1,'r')
    except Exception as e:
        print("open file failed")
        print(str(e))
    else:
        print("open file ok")
        w_fp.write('Tx-Idx' + ',' + 'Tx-L' + ',' + 'Tx-M' + ',' + 'Tx-R' + ',' + 'Dev-Rx' + ',' \
                'Rx-Idx' + ',' + 'Rx-L' + ',' + 'Rx-M' + ',' + 'Rx-R' + ',' + 'Dev-Tx' + '\n')
        w2_fp.write('GroupIdx' + ',' + 'Rx DFT Std' + ',' + 'Rx Dev Std' + ',' + 'Tx-DFT-Std' + ',' + 'Tx Dev Std' + '\n')
        array_dev_rx = [[] for i in range(30)]
        array_dev_tx = [[] for i in range(30)]
        array_dft_rx = [[] for i in range(30)]
        array_dft_tx = [[] for i in range(30)]

        #print(len(array_dft_rx))
        index = 0

        group_idx = -1
        pre_idx = now_idx = 0


        '''
        Take DFT Power/Deviation from file into array
        and compute to Std
        '''
        for line in fp:
            content = line.strip().split(' ')
            #for i, value in enumerate(content):                
                #if (value == '[DEBUG_PEN]17'):
                #if (value == '17'):
            #if (content[0] == '17'):   
            if (content[0] == '[DEBUG_PEN]17'):
                    index = index + 1
                    
                    index_rx = content[10]
                    index_rx = int(index_rx, 16)
                    index_tx = content[26]
                    index_tx = int(index_tx, 16)
                    rx_dft_power_l = "".join([content[3], content[2]])
                    rx_dft_power_l = int(rx_dft_power_l, 16)
                    rx_dft_power_m = "".join([content[5], content[4]])
                    rx_dft_power_m = int(rx_dft_power_m, 16)
                    rx_dft_power_r = "".join([content[7], content[6]])
                    rx_dft_power_r = int(rx_dft_power_r, 16)
                    deviation_rx = "".join([content[9], content[8]])
                    hex_dev_rx = int(deviation_rx,16)
                    deviation_rx = np.int16(hex_dev_rx) #unsigned to signed
                                          
                    #print(rx_dft_power_m)
                    #print(array_dft_rx[group_idx])                        
                    array_dft_rx[group_idx].append(rx_dft_power_m)
                    array_dev_rx[group_idx].append(deviation_rx)

                    
                    tx_dft_power_l = "".join([content[19], content[18]])
                    tx_dft_power_l = int(tx_dft_power_l, 16)
                    tx_dft_power_m = "".join([content[21], content[20]])
                    tx_dft_power_m = int(tx_dft_power_m, 16)
                    tx_dft_power_r = "".join([content[23], content[22]])
                    tx_dft_power_r = int(tx_dft_power_r, 16)
                    deviation_tx = "".join([content[25], content[24]])
                    hex_dev_tx = int(deviation_tx,16)
                    deviation_tx = np.int16(hex_dev_tx)

                    array_dft_tx[group_idx].append(tx_dft_power_m)
                    array_dev_tx[group_idx].append(deviation_tx)

                    #Tx
                    #now_idx = int(content[26],16)
                    #Rx
                    now_idx = int(content[10],16)
                    if (now_idx != pre_idx):
                        
                        if (group_idx >= 0):
                            print("GroupIdx=%d Rx DFT Std=%f, Dev Std=%f, Tx DFT Std=%f, Dev Std=%f\n" %
                              (group_idx, np.std([array_dft_rx[group_idx]], ddof=1), np.std([array_dev_rx[group_idx]], ddof=1),
                               np.std([array_dft_tx[group_idx]], ddof=1), np.std([array_dev_tx[group_idx]], ddof=1)))
                        
                            w2_fp.write(str(group_idx) + ',' + str(np.std([array_dft_rx[group_idx]], ddof=1)) + ',' + str(np.std([array_dev_rx[group_idx]], ddof=1)) + ',' \
                                        + str(np.std([array_dft_tx[group_idx]], ddof=1)) + ',' + str(np.std([array_dev_tx[group_idx]], ddof=1)) + '\n')

                        group_idx = group_idx + 1
                        pre_idx = now_idx
                    
                    w_fp.write(str(index_rx) + ',' + str(rx_dft_power_l) + ',' + str(rx_dft_power_m) + ',' + str(rx_dft_power_r) + ',' + str(deviation_rx) + ',')
                    w_fp.write(str(index_tx) + ',' + str(tx_dft_power_l) + ',' + str(tx_dft_power_m) + ',' + str(tx_dft_power_r) + ',' + str(deviation_tx) + '\n')

        # Sorting DFT Power Rx/Tx buffer                
        for i in xrange(group_idx):
            array_dft_rx[i].sort()
            array_dft_tx[i].sort()
        

        # average DFT Power by index
        line = 0
        for i in xrange(group_idx):            
            line += 1
            count_rx = 0
            count_tx = 0
            avg_dft_rx = 0
            avg_dft_tx = 0
            for dft_rx, dft_tx in itertools.izip_longest(array_dft_rx[i], array_dft_tx[i], fillvalue=''):              
                avg_dft_tx += dft_tx
                count_tx += 1
                avg_dft_rx += dft_rx
                count_rx += 1
           
            w3_fp.write(str(line) + ',' + str(avg_dft_rx / count_rx) + ',' + str(avg_dft_tx / count_tx) + '\n')

        

                
# Entry
w_fp = open(w_SANKE_P1, 'w')
w2_fp = open(w2_SANKE_P1, 'w')
w3_fp = open(w3_SANKE_P1, 'w')
DFT_Power_Parser()
w_fp.close()
w2_fp.close()
w3_fp.close()

# matplotlib plot, file located C:\Python27\Lib\site-packages\matplotlib\mpl-data\sample_data
fname = cbook.get_sample_data('Snake_w3.txt', asfileobj=False)
#plt.plotfile(fname, cols=(0,1,2,3))#, plotfuncs={2: 'semilogy'})
#ax = plt.subplots()
#ax.set_color_cycle(['red'])
plt.plotfile(fname, cols=(0,1,2), subplots=True)#, color='blue')
#plt.plotfile(fname, cols=(5,2,7), subplots=False)
plt.xlabel(r'$Rx Index$')
plt.show()



'''
fname = cbook.get_sample_data('msft.csv', asfileobj=False)
fname2 = cbook.get_sample_data('data_x_x2_x3.csv', asfileobj=False)
DFT_Power_Parser()
# test 1; use ints
# plt.plotfile(fname, (0, 2, 5, 6))

# test 2; use names
# plt.plotfile(fname, ('date', 'volume', 'adj_close'))

# test 3; use semilogy for volume
#plt.plotfile(fname, ('date', 'volume', 'adj_close'),
#             plotfuncs={'volume': 'semilogy'})

# test 4; use semilogy for volume
#plt.plotfile(fname, (0, 5, 6), plotfuncs={5: 'semilogy'})

# test 5; single subplot
plt.plotfile(fname, ('date', 'open', 'high', 'low', 'close'), subplots=False)

# test 6; labeling, if no names in csv-file
plt.plotfile(fname2, cols=(0, 1, 2), delimiter=' ',
             names=['$x$', '$f(x)=x^2$', '$f(x)=x^3$'])

# test 7; more than one file per figure--illustrated here with a single file
plt.plotfile(fname2, cols=(0, 1), delimiter=' ')
plt.plotfile(fname2, cols=(0, 2), newfig=False,
             delimiter=' ')  # use current figure
plt.xlabel(r'$x$')
plt.ylabel(r'$f(x) = x^2, x^3$')

# test 8; use bar for volume
plt.plotfile(fname, (0, 5, 6), plotfuncs={5: 'bar'})

plt.show()
'''