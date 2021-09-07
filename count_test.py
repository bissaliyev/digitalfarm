#!/usr/bin/env python3
import os
from datetime import datetime
import RPi.GPIO as GPIO
import busio
import serial
import wiringpi

RFID_PORT = '/dev/ttyS0'
# TABLO_PORT1 = '/dev/ttyACM0'
# TABLO_PORT2 = '/dev/ttyACM1'
# WEIGHT_PORT1 = '/dev/ttyUSB0'
# WEIGHT_PORT2 = '/dev/ttyUSB1'
DIGITAL_FARM_URL = 'digitalfarm.kz'
# DIGITAL_FARM_URL = '178.170.221.174:5000'

os.system('sudo fuser -k /dev/ttyACM0')
os.system('sudo fuser -k /dev/ttyACM1')
# os.system('sudo fuser -k /dev/ttyS0')
# try:
#     TB_SER = serial.Serial(TABLO_PORT1, 115200, timeout=1)
# except:
#     TB_SER = serial.Serial(TABLO_PORT2, 115200, timeout=1)
RF_ser = serial.Serial(RFID_PORT, baudrate=115200, timeout=1)

FILE_READ = '/home/pi/Desktop/setup.txt'
USB_OFF = 'echo \'1-1\' | sudo tee /sys/bus/usb/drivers/usb/unbind'
USB_ON = 'echo \'1-1\' | sudo tee /sys/bus/usb/drivers/usb/bind'
HDMI_OFF = 'sudo vcgencmd display_power 0'
HDMI_ON = 'sudo vcgencmd display_power 1'
i2c = busio.I2C(3, 2)
# am = adafruit_am2320.AM2320(i2c)
tb_t = 0
tmp_t = 0
weight = 0
wgt = 0
temp = 0
a = 0
alarm = 0
state = 1
sendpost = 0
online = 0
count = 0
cnt = [0]
wg = [0]
msg_list = [""]
prepare = 3
phase = 0
inputByte = 0
inputBytes = [0] * 5
inputByte_1 = 0
inputByte_2 = 0
inputByte_3 = 0
hexBytes = [hex(0)] * 100
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


while 1:
    # Serial READ
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
                # print(tag_id)

                print('------------------')
                msg = ""
                rssi = ""
                ant = -1
                ant = int(tag_id[34:36])
                rssi = tag_id[length * 2 + 4: len(tag_id)]
                msg = tag_id[36: length * 2 + 4]

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

                # =============================
                for i in range(len(msg_list)):
                    perm = msg in msg_list[i]
                    if perm == True:
                        num = i
                        cnt[i] = cnt[i] + 1
                        # wg[i] = weighting()
                        break
                if perm == False:
                    num = len(msg_list) - 1
                    msg_list[len(msg_list) - 1] = str(msg)
                    msg_list.append("")
                    cnt.append(1)
                    wg.append(1)
                # _____________________________
                perm = 0
                flag = 0
                # =============================
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

                count = count + 1
                print(len(id_list) - 1)
