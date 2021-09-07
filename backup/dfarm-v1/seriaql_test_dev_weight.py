#!/usr/bin/env python3
import RPi.GPIO as GPIO
import serial
import binascii
import codecs 
import numpy as np
from time import sleep
from datetime import datetime
import requests
import json
import keyboard
import sys # Прерыватель
import os
from tkinter import *
from tkinter import messagebox
import tkinter
import board
import digitalio
import busio
import wiringpi
import adafruit_am2320
from signal import signal, SIGINT
from sys import exit

RFID_PORT = '/dev/ttyS0'
TABLO_PORT1 = '/dev/ttyACM0'
TABLO_PORT2 = '/dev/ttyACM1'
WEIGHT_PORT1 = '/dev/ttyUSB0'
WEIGHT_PORT2 = '/dev/ttyUSB1'
DIGITAL_FARM_URL = 'digitalfarm.kz'
#DIGITAL_FARM_URL = '178.170.221.174:5000'

os.system('sudo fuser -k /dev/ttyACM0')
os.system('sudo fuser -k /dev/ttyACM1')
#os.system('sudo fuser -k /dev/ttyS0')
try:
    TB_SER = serial.Serial(TABLO_PORT1, 115200, timeout=1)
except:
    TB_SER = serial.Serial(TABLO_PORT2, 115200, timeout=1)
RF_ser = serial.Serial(RFID_PORT, baudrate = 115200, timeout = 1)
try:
    #os.system('sudo fuser -k /dev/ttyUSB0')
    WG_ser = serial.Serial(WEIGHT_PORT1,
                    baudrate=4800,
                    parity=serial.PARITY_EVEN,
                    #stopbits=serial.STOPBITS_ONE,
                    #eits=serial.EIGHTBITS,
                    timeout = 1)
except:
    #os.system('sudo fuser -k /dev/ttyUSB1')
    WG_ser = serial.Serial(WEIGHT_PORT2,
                    baudrate=4800,
                    parity=serial.PARITY_EVEN,
                    #stopbits=serial.STOPBITS_ONE,
                    #eits=serial.EIGHTBITS,
                    timeout = 1)
FILE_READ = '/home/pi/Desktop/setup.txt'
USB_OFF = 'echo \'1-1\' | sudo tee /sys/bus/usb/drivers/usb/unbind'
USB_ON = 'echo \'1-1\' | sudo tee /sys/bus/usb/drivers/usb/bind'
HDMI_OFF = 'sudo vcgencmd display_power 0'
HDMI_ON = 'sudo vcgencmd display_power 1'
i2c = busio.I2C(3, 2)
am = adafruit_am2320.AM2320(i2c)
tb_t = 0
tmp_t = 0
weight = 0
wgt = 0
temp = 0
a = 0
alarm = 0
state = 0
sendpost = 0
online = 0
count = 0
cnt = [0]
wg = [0]
msg_list = [""]
prepare = 3
phase = 0
inputByte = 0
inputBytes = [0]*5
inputByte_1 = 0
inputByte_2 = 0
inputByte_3 = 0
hexBytes = [hex(0)]*100
time_start1 = ''
time_end1 = ''
time_start2 = ''
time_end2 = ''
name = ""
h_now = ''
m_now = ''
data_list = ''

tag_id = ""
msg = ""
ant = -1
rssi = ""
length = 0
id_list = [""]
ant1_list = [-1]
ant2_list = [-1]
ant3_list = [-1]
ant4_list = [-1]
cnt1_list = [0]
cnt2_list = [0]
cnt3_list = [0]
cnt4_list = [0]
rssi_list = [""]
length_list = [0]

num = 0

cnt_ir = [0]
ir_true = [0] * 4
ir_check = 0
ir_t = [0] * 4
ir_cc = [0] * 4
ir_num = [0] * 4

time = datetime.today()
h_now = time.hour
m_now = time.minute
print('time')
print(h_now)
print(m_now)
print('')
ts1_h =0
ts1_m = 0
te1_h = 0
te1_m = 0
ts2_h = 0
ts2_m = 0
te2_h = 0
te2_m = 0
tmp_lvl = 0

irpin = [0] * 4
irpin[0] = 18
irpin[1] = 23
irpin[2] = 24
irpin[3] = 25 
ir_ch1_max = 0
ir_ch2_max = 0
GPIO.setmode(GPIO.BCM)
GPIO.setup(irpin[0], GPIO.IN)
GPIO.setup(irpin[1], GPIO.IN)
GPIO.setup(irpin[2], GPIO.IN)
GPIO.setup(irpin[3], GPIO.IN)
    
def proctemp():
    global temp
    try:
            temp = am.temperature
            #print("\r Temperature: {0:.2f}°F Humidity: {1:.2f}%".format(round(temp,1), round(am.relative_humidity,1)), end='')
    except:
        return False
    return temp

def weighting():
    global weight, inputBytes
    print('weighting connect...')
    perm = 1
    delay = wiringpi.millis()
    while perm:
        perm = 1
        WG_ser.write('E'.encode('utf-8'))
        sleep(0.001)
        error = wiringpi.millis()
        while WG_ser.inWaiting() == 0:
            if wiringpi.millis() - error >= 1000:
                perm = 0
                weight = None
                break
        if WG_ser.inWaiting() > 0 and perm:
            msg = ""
            a = 0
            while WG_ser.inWaiting():
                #print(a)
                inputBytes[a] = WG_ser.read()
                if a < 2 :
                    a = a + 1
            msg = str(inputBytes[1]) + str(inputBytes[0])
            byt = inputBytes[1] + inputBytes[0]
            byt = int.from_bytes(byt, byteorder='big')
            weight = byt/100
            print(weight)
            if weight < 1:
                delay = wiringpi.millis()
            
        if wiringpi.millis() - delay >= 3000:
            perm = 0
    print('weight = ' + str(weight))
    return weight

def timemng():
    global name, ts1_h, ts1_m, te1_h, te1_m, ts2_h, ts2_m, te2_h, te2_m, tmp_lvl
    #print('setup.txt:')
    try:
        f = open(FILE_READ)
    except ValueError as e:
        return False
    for line in f :
        if line.find("NAME=") == 0 :
            name = line
        if line.find("TIME_START1=") == 0 :
            time_start1 = line
        if line.find("TIME_END1=") == 0 :
            time_end1 = line
        if line.find("TIME_START2=") == 0 :
            time_start2 = line
        if line.find("TIME_END2=") == 0 :
            time_end2 = line
        if line.find("TEMP=") == 0 :
            ss_tmp_lvl = line
    name = name[name.find("=") + 1 : len(name) - 1]
    ss_tmp_lvl = ss_tmp_lvl[ss_tmp_lvl.find("=") + 1 : len(ss_tmp_lvl)]
    tmp_lvl = int(ss_tmp_lvl)
    ts1_h = int(time_start1[time_start1.find("TIME_START1=") + 12 : time_start1.find(":")])
    ts1_m = int(time_start1[time_start1.find(":") + 1 : len(time_start1)])
    te1_h = int(time_end1[time_end1.find("TIME_END1=") + 10 : time_end1.find(":")])
    te1_m = int(time_end1[time_end1.find(":") + 1 : len(time_end1)])
    ts2_h = int(time_start2[time_start2.find("TIME_START2=") + 12 : time_start2.find(":")])
    ts2_m = int(time_start2[time_start2.find(":") + 1 : len(time_start2)])
    te2_h = int(time_end2[time_end2.find("TIME_END2=") + 10 : time_end2.find(":")])
    te2_m = int(time_end2[time_end2.find(":") + 1 : len(time_end2)])
    #print('')
    #print(tmp_lvl)
    #print('')
    '''
    print(ts1_h)
    print(ts1_m)
    print('')
    print(te1_h)
    print(te1_m)
    print('')
    print(ts2_h)
    print(ts2_m)
    print('')
    print(te2_h)
    print(te2_m)
    '''

def is_json(f):
    try:
        file = open(f)
    except IOError:
        return False
    try:
        with open(f) as json_file:
            json_object = json.load(json_file)
    except ValueError as e:
        return False
    return True

def writeFile():
    global name, count, cnt, wg, data_list, msg, msg_list, num, state, time
    time = datetime.today()
    
    if state == 1 :
        FILE_WRITE = '/home/pi/Documents/data/weight_m_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'
    elif state == 2 :
        FILE_WRITE = '/home/pi/Documents/data/weight_e_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'
    #check file
    # first tid
    if len(msg_list) > 1 :
        clear_file(FILE_WRITE)
        data_list = {"date":time.strftime("%Y-%m-%d"),
        "company_code":str(name),
        "data": [{
            "no":count,
            "time": time.strftime("%H:%M:%S"),
            "tag_id":msg_list[0],
            "weight":wg[0],
            "cnt":str(cnt[0])}]
        }
        with open(FILE_WRITE, 'w') as jf:
            json.dump(data_list, jf, indent=4)
    # other tids
        if len(msg_list) - 1 > 0:
            if is_json(FILE_WRITE) == True:
                for i in range(1, len(msg_list) - 1):
                    with open(FILE_WRITE) as json_file:
                        data_list = json.load(json_file)
                        new_data = {
                        "no":count,
                        "time":time.strftime("%Y-%m-%d"),
                        "tag_id":msg_list[i],
                        "weight":wg[i],
                        "cnt":str(cnt[i])
                        }
                        temp = data_list['data']
                        temp.append(new_data)
                #print(json.dumps(data_list))
                    with open(FILE_WRITE, 'w') as jf:
                        json.dump(data_list, jf, indent=4)
                        
def writePARFile():
    global name, count, cnt, wg, data_list, msg, num, state, time, cnt1_list, cnt2_list, cnt3_list, cnt4_list, id_list, rssi_list, length_list
    time = datetime.today()
    
    if state == 1 :
        FILE_WRITE = '/home/pi/Documents/data/weight_m_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'
    elif state == 2 :
        FILE_WRITE = '/home/pi/Documents/data/weight_e_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'
    #check file
    # first tid
    clear_file(FILE_WRITE)
    data_list = {"date":time.strftime("%Y-%m-%d"),
        "company_code":str(name),
        "data": [{
            "time": time.strftime("%H:%M:%S"),
            "tag_id":id_list[0],
            "weight":wg[0],
            "length":length_list[0],
            "ant1":cnt1_list[0],
            "ant2":cnt2_list[0],
            "ant3":cnt3_list[0],
            "ant4":cnt4_list[0],
            "cnt":str(cnt1_list[0] + cnt2_list[0] + cnt3_list[0] + cnt4_list[0]),
            "RSSI":rssi_list[0]
            }]
    }
    with open(FILE_WRITE, 'w') as jf:
        json.dump(data_list, jf, indent=4)
    # other tids
    
    if len(id_list) - 1 > 0:
        if is_json(FILE_WRITE) == True:
            for i in range(1, len(id_list) - 1):
                with open(FILE_WRITE) as json_file:
                    data_list = json.load(json_file)
                    new_data = {
                            "time": time.strftime("%H:%M:%S"),
                            "tag_id":id_list[i],
                            "weight":wg[i],
                            "length":length_list[i],
                            "ant1":cnt1_list[i],
                            "ant2":cnt2_list[i],
                            "ant3":cnt3_list[i],
                            "ant4":cnt4_list[i],
                            "cnt":str(cnt1_list[i] + cnt2_list[i] + cnt3_list[i] + cnt4_list[i]),
                            "RSSI":rssi_list[i]
                    }
                    temp = data_list['data']
                    temp.append(new_data)
                #print(json.dumps(data_list))
                with open(FILE_WRITE, 'w') as jf:
                    json.dump(data_list, jf, indent=4)
                        
def clear_file(f):
    try:
        f = open(f, 'w')
        f.truncate(0)
    except:
        True
def show(key):
    print('\nWrite PAR File {0}'.format( key))
    if key == Key.delete:
        return False
'''    
def writeFileIR():
    global name, count, cnt, wg, data_list, msg, msg_list, num, state
    time = datetime.today()
    
    
        
    if state == 1 :
        FILE_WRITE = '/home/pi/Documents/data/rfid_m_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'
    elif state == 2 :
        FILE_WRITE = '/home/pi/Documents/data/rfid_e_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'
    #check file
    # first tid
    if len(msg_list) > 1 :
        clear_file(FILE_WRITE)
        data_list = {"date":time.strftime("%Y-%m-%d"),
        "company_code":str(name),
        "data": [{
            "no":count,
            "time":time.strftime("%H:%M:%S"),
            "tag_id":msg_list[0],
            "cnt":str(cnt[0])}]
        }
        with open(FILE_WRITE, 'w') as jf:
            json.dump(data_list, jf, indent=4)
    # other tids
        if len(msg_list) - 1 > 0:
            if is_json(FILE_WRITE) == True:
                for i in range(1, len(msg_list) - 1):
                    with open(FILE_WRITE) as json_file:
                        data_list = json.load(json_file)
                        new_data = {
                        "no":count,
                        "time":str(time.strftime("%Y-%m-%d")),
                        "tag_id":msg_list[i],
                        "cnt":str(cnt[i])
                        }
                        temp = data_list['data']
                        temp.append(new_data)
                #print(json.dumps(data_list))
                    with open(FILE_WRITE, 'w') as jf:
                        json.dump(data_list, jf, indent=4)
'''                        
def post(url, js):
    global online
    try :
        request = requests.post(url, json=js)
    except IOError:
        return False
    ss = request.text
    #print(ss[0:40])
    #print(ss)
    print(js)
    if ss.find('success') >= 0:
        online = 1
        return True
    else :
        online = 0
        return False

timemng()
while 1:
    cur = wiringpi.millis()
    #global ts1_h, ts1_m, te1_h, te1_m, ts2_h, ts2_m, te2_h, te2_m
    #global name, prepare, state, count, cnt, wg, a, online, sendpost, data_list, msg, msg_list, num, temp, tmp_lvl
    #global USB_ON, USB_OFF
    #global HDMI_ON, HDMI_OFF
    if h_now * 60 + m_now >= ts1_h * 60 + ts1_m and h_now * 60 + m_now <= te1_h * 60 + te1_m :
        state = 1 
        sendpost = 1
    if h_now * 60 + m_now >= ts2_h * 60 + ts2_m and h_now * 60 + m_now <= te2_h * 60 + te2_m :
        state = 2
        sendpost = 1
    #print(str(h_now * 60 + m_now) + '>=' + str(ts1_h * 60 + ts1_m) + ' ' + str(h_now * 60 + m_now) + '<=' + str(te1_h * 60 + te1_m))
    #print(str(h_now * 60 + m_now) + '>=' + str(ts2_h * 60 + ts2_m) + ' ' + str(h_now * 60 + m_now) + '<=' + str(te2_h * 60 + te2_m))
    if (h_now * 60 + m_now >= ts1_h * 60 + ts1_m and h_now * 60 + m_now <= te1_h * 60 + te1_m) == 0 and (h_now * 60 + m_now >= ts2_h * 60 + ts2_m and h_now * 60 + m_now <= te2_h * 60 + te2_m) == 0 :
        # send data when work is ending
        if online == 1:
            if sendpost == 1:
                sendpost = 0
                writeFile()
                print("main")
                print("----------------------")
                print(data_list)
                #post('http://178.170.221.174:5000/loadMove', data_list)
                post(f'http://{DIGITAL_FARM_URL}/loadMove', data_list)
                writePARFile()
                print("second")
                print("----------------------")
                print(data_list)
                post(f'http://{DIGITAL_FARM_URL}/loadMove', data_list)
                count = 0
        if state == 2 :
            os.system("sudo shutdown")
        state = 0
    '''
    print(state)
    print(h_now * 60 + m_now)
    print(ts1_h * 60 + ts1_m)
    print(te1_h * 60 + te1_m)
    print(ts2_h * 60 + ts2_m)
    print(te2_h * 60 + te2_m)
    
    '''
    #print(str(96.57//1)+ ' ' + str(96.57*100%100))
    if cur - tb_t >= 2000:
        timemng()
        var = "A" + str(len(cnt) - 1)  + "B" + str(int(wgt//1)) + '' + str(int(wgt*100%100)) + "C\r\n"
        TB_SER.write(str.encode(var))
        time = datetime.today()
        h_now = time.hour
        m_now = time.minute
        #print(str.encode(var))
        tb_t = cur
    if cur - tmp_t >= 2000:
        proctemp()
        tmp_t = cur
    #print(count)
    #
       # print(temp)
        if tmp_lvl < temp and alarm == 0:
            temp_alr = {"date":time.strftime("%Y-%m-%d") + ' ' + time.strftime("%H:%M:%S"),
                    "company_code":str(name),
                    "data": [{
                        "time":time.strftime("%H:%M:%S"),
                       "tag_id":"temp alert"
                    }
                 ]
            }
            print('temp is high = warning')
            alarm = 1
            if post(f'http://{DIGITAL_FARM_URL}/statusResult', temp_alr) == True: # now is online
            #if post('http://178.170.221.174:5000/statusResult', temp_alr) == True: # now is online
                online = 1
                alarm = 1
        else:
            alarm = 0
        
    if state > 0 : # linux on hdmi usb
        if prepare < 6 :
            prepare = prepare + 1
            #os.system(USB_ON)
            #os.system(HDMI_ON)
        # check online
        if online == 0: # is offline
            print('ready:' + str(time.strftime("%Y-%m-%d")) + str(time.strftime("%H:%M:%S")))
            
            ok = {"date":time.strftime("%Y-%m-%d") + ' ' + time.strftime("%H:%M:%S"),
                "company_code":str(name),
                "data": [{
                    "time":time.strftime("%H:%M:%S"),
                    "temp":str(temp),
                    "tag_id":"is_ready"
                }
              ]
            }
            #print(ok)
            if post(f'http://{DIGITAL_FARM_URL}/statusResult', ok) == True: # now is online
                online = 1
                print('online')
            else:
                print('offline')
    if state == 0 : # linux off hdmi usb
        if prepare > 0 :
            prepare = prepare - 1
            #os.system(USB_OFF)
            #os.system(HDMI_OFF)
    #ir read
    if state > 0 :
        #print("sta : " + str(GPIO.input(irpin[0])) + " " +str(GPIO.input(irpin[1])) + " " +str(GPIO.input(irpin[2])) + " " +str(GPIO.input(irpin[3])))
        #print("num : " + str(ir_ch1_max) + " " +str(ir_ch2_max))
        #print(ir_ch1_max+ir_ch2_max)
        #print(ir_num[0])#
        #print(ir_num[1])
        #print(ir_num[2])
        #print(ir_num[3])
        for i in range(0, 4):
            if GPIO.input(irpin[i]) == GPIO.LOW:
                if ir_cc[i] == 0:
                    ir_cc[i] = 1
                    ir_t[i] = wiringpi.millis()
            elif GPIO.input(irpin[i]) == GPIO.HIGH:
                if ir_cc[i] == 1:
                    ir_cc[i] = 0
                    if wiringpi.millis() - ir_t[i] >= 100:
                        ir_num[i] = ir_num[i] + 1
        if ir_num[0] > ir_num[2]:
            ir_ch1_max = ir_num[0]
        else:
            ir_ch1_max = ir_num[2]
        if ir_num[1] > ir_num[3]:
            ir_ch2_max = ir_num[1]
        else:
            ir_ch2_max = ir_num[3]
        '''
        if GPIO.input(irpin1) == GPIO.LOW:
            if ir_cc1 == 0:
                ir_cc1 = 1
                ir_true1 = 0
                ir_t1 = cur
            elif  ir_cc1 == 1 and cur - ir_t1 >= 300:
                ir_cc1 = 0
                if ir_true1 == 1:
                    print("ir 1 birka read1")
                else:
                    print("ir 1 birka not read1") 
                ir_num = ir_num + 1
                print("ir_num=" + str(ir_num))
        elif GPIO.input(irpin1) == GPIO.HIGH :
            if ir_cc1 == 1:
                if cur - ir_t1 >= 1000:
                    ir_cc1 = 0
                    if ir_true1 == 1:
                        print("ir 1 birka read2")
                    else:
                        print("ir 1 birka not read2")
                        ir_num = ir_num + 1
                    print("ir_num=" + str(ir_num))
        
        if GPIO.input(irpin2) == GPIO.LOW :
            if ir_cc2 == 0:
                ir_cc2 = 1
                ir_true2 = 0
                ir_t2 = cur
            elif  ir_cc2 == 1 and cur - ir_t2 >= 200:
                ir_cc2 = 0
                if ir_true2 == 1:
                    print("ir 2 birka read1")
                else:
                    print("ir 2 birka not read1") 
        elif GPIO.input(irpin2) == GPIO.HIGH :
            if ir_cc2 == 1:
                if cur - ir_t2 >= 1000:
                    ir_cc2 = 0
                    if ir_true2 == 1:
                        print("ir 2 birka read2")
                    else:
                        print("ir 2 birka not read2")
        '''
    # Serial READ
    #weighting()
    if RF_ser.inWaiting() > 0 and state > 0:
        inputByte = RF_ser.read()
        if inputByte == b'\x43':
            inputByte = RF_ser.read(2)
            if inputByte.hex() == "5400":
                tag_id = "435400"
                inputByte = RF_ser.read(1)
                length = int(inputByte.hex(), 16)
                tag_id = tag_id + str(inputByte.hex())
                inputByte = RF_ser.read(length)
                tag_id = tag_id + str(inputByte.hex())
                #print(tag_id)
                
                print('------------------')
                msg = ""
                rssi = ""
                ant = -1
                ant = int(tag_id[34:36])
                rssi = tag_id[length * 2 + 4 : len(tag_id)]
                msg = tag_id[36 : length * 2 + 4]
                    
                    
                print('id = ' + msg)
                print('antena №' + str(ant))
                print('RSSI = ' + rssi)
                print('Length = ' + str(length))
                print('')
                print('------------------')
                    
                ir_true1 = 1
                ir_true2 = 1
                perm = 0
                flag = 0
                num = 0

                #=============================
                for i in range(len(msg_list)):
                    perm = msg in msg_list[i]
                    if perm == True:
                        num = i
                        cnt[i] = cnt[i] + 1
                        #wg[i] = weighting()
                        break
                if perm == False:
                    num = len(msg_list) - 1
                    msg_list[len(msg_list) - 1] = str(msg)
                    msg_list.append("")
                    cnt.append(1)
                    wg.append(1)
                #_____________________________
                perm = 0
                flag = 0
                #=============================
                for i in range(len(id_list)):
                    perm = msg in id_list[i]
                    if perm == True:
                        num = i
                        if ant == 1:
                            cnt1_list[i] = cnt1_list[i] + 1
                        elif ant == 2:
                            cnt2_list[i] = cnt2_list[i] + 1
                        elif ant == 3:
                            cnt3_list[i] = cnt3_list[i] + 1
                        elif ant == 4:
                            cnt4_list[i] = cnt4_list[i] + 1
                        length_list[i] = length
                        rssi_list[i] = rssi
                        break
                if perm == False:
                    num = len(id_list) - 1
                        
                    id_list[len(id_list) - 1] = str(msg)
                    id_list.append("")
                        
                    length_list[len(length_list) - 1] = length
                    length_list.append(0)
                        
                    rssi_list[len(rssi_list) - 1] = rssi
                    rssi_list.append("")
                    
                    if ant == 1:   
                        cnt1_list[len(cnt1_list) - 1] = 1
                    elif ant == 2:
                        cnt2_list[len(cnt2_list) - 1] = 1
                    elif ant == 3:
                        cnt3_list[len(cnt3_list) - 1] = 1
                    elif ant == 4:
                        cnt4_list[len(cnt4_list) - 1] = 1

                    cnt1_list.append(0)
                    cnt2_list.append(0)
                    cnt3_list.append(0)
                    cnt4_list.append(0)
                        
                    wg[i] = weighting()
                    wgt = wg[i]
                        
                    #_____________________________
                     
                count = count + 1
                print(len(id_list) - 1)
                print(wg)
                '''
                print(id_list)
                print(length_list)
                print(rssi_list)
                print(cnt1_list)
                print(cnt2_list)
                print(cnt3_list)
                print(cnt4_list)
                '''     
                    
    
            
    # update display
    #w1.config(text = len(cnt) - 1)
    #root.after(1, main)
    
#root = tkinter.Tk()
#root.title('test')
#root.minsize(200, 100)
#w1 = tkinter.Label(root, text = len(cnt) - 1)
#w1.pack()
#root.after(1, main)
#root.mainloop()
'''
try:
except KeyboardInterrupt: # Прерывание с клавиатуры ctrl+C
    output = int(input('r - Вывод в файл '))
    if(output == 'r'):
        print('Вывод в файл')
        writePARFile()
'''




