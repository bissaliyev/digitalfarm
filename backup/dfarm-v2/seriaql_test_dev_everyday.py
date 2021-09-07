#!/usr/bin/env python3
import json
import logging
import os
import socket
from datetime import datetime

import RPi.GPIO as GPIO
import requests
import serial

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

fileHandler = logging.FileHandler("/home/pi/digitalfarm.log")
fileHandler.setFormatter(logFormatter)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

RFID_PORT = '/dev/ttyS0'
WEIGHT_PORT1 = '/dev/ttyUSB0'
WEIGHT_PORT2 = '/dev/ttyUSB1'
LOAD_URL = 'http://digitalfarm.kz/loadMove'
STATUS_URL = 'http://digitalfarm.kz/statusResult'

try:
    RF_ser = serial.Serial(RFID_PORT, baudrate=115200, timeout=1)
except:
    logger.error("Could not connect to RFID")

tb_t = 0
tmp_t = 0
weight = 0
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
phase = 0
inputByte = 0
inputBytes = []
inputByte_1 = 0
inputByte_2 = 0
inputByte_3 = 0
hexBytes = [hex(0)] * 100
name = ""
data_list = ''

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

GPIO.setmode(GPIO.BCM)

# Switch settings
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(31, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # switch 1 (BOARD 29 / BCM 5)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # switch 2 (BOARD 31 / BCM 6)

def is_mode_count_rfid_and_weight():
    return GPIO.input(29) == GPIO.LOW
def is_mode_count_rfid():
    return GPIO.input(31) == GPIO.LOW
def is_mode_send_data():
    return GPIO.input(29) == GPIO.HIGH and GPIO.input(31) == GPIO.HIGH


def is_connected_to_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.error("Could not connect to internet: " + ex)
        return False


def is_server_online(url):
    try:
        response = requests.head(url)
    except IOError:
        logger.error("Server is offline")
        return False

    if response.status_code == requests.codes.ok:
        try:
            json_data = {
                "date": time.strftime("%Y-%m-%d") + ' ' + time.strftime("%H:%M:%S"),
                "company_code": str(name),
                "data": [
                    {
                        "time": time.strftime("%H:%M:%S"),
                        "tag_id": "is_ready"
                    }
                ]
            }
            response = requests.post(url, json=json_data)
        except IOError as ex:
            logger.error("Server status check failed " + ex)
            return False

        if response.status_code == requests.codes.ok and response.text.find('success') >= 0:
            logger.info("Server is online")
            return True
        else:
            logger.info('Server is offline')
            return False


def is_json(f):
    try:
        with open(f) as json_file:
            json.load(json_file)
    except IOError:
        logging.error("Could not open file: " + str(f))
        return False
    except ValueError:
        logging.error("File is not in JSON format: " + str(f))
        return False
    return True


def writePARFile():
    global name, count, cnt, wg, data_list, msg, num, state, time, cnt1_list, cnt2_list, cnt3_list, cnt4_list, id_list, rssi_list, length_list

    logger.info("Started writing data file")

    time = datetime.today()

    FILE_WRITE = '/home/pi/data/rfid_' + str(time.strftime("%Y-%m-%d")) + ' ' + str(time.strftime("%H:%M:%S")) + '.txt'

    # check file
    # first tid
    clear_file(FILE_WRITE)
    data_list = {
        "date": time.strftime("%Y-%m-%d"),
        "company_code": str(name),
        "data": [
            {
                "time": time.strftime("%H:%M:%S"),
                "tag_id": id_list[0],
                "length": length_list[0],
                "ant1": cnt1_list[0],
                "ant2": cnt2_list[0],
                "ant3": cnt3_list[0],
                "ant4": cnt4_list[0],
                "cnt": str(cnt1_list[0] + cnt2_list[0] + cnt3_list[0] + cnt4_list[0]),
                "RSSI": rssi_list[0]
            }
        ]
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
                        "tag_id": id_list[i],
                        "length": length_list[i],
                        "ant1": cnt1_list[i],
                        "ant2": cnt2_list[i],
                        "ant3": cnt3_list[i],
                        "ant4": cnt4_list[i],
                        "cnt": str(cnt1_list[i] + cnt2_list[i] + cnt3_list[i] + cnt4_list[i]),
                        "RSSI": rssi_list[i]
                    }
                    temp = data_list['data']
                    temp.append(new_data)
                with open(FILE_WRITE, 'w') as jf:
                    json.dump(data_list, jf, indent=4)

    logger.info("Finished writing data file")


def clear_file(f):
    try:
        f = open(f, 'w')
        f.truncate(0)
    except:
        logger.error("Could not open clear file")


def show(key):
    logger.debug('Write PAR File {0}'.format(key))
    if key == Key.delete:
        return False


def send_data_to_server(url, json_data):
    global online
    logger.info("Started data file upload")
    response = ""
    try:
        response = requests.post(url, json=json_data)
    except IOError:
        logger.error("Could not upload data file to server")
        return False
    finally:
        if response.text.find('success') >= 0:
            logger.info("Finished data file upload")
            return True
        else:
            logger.error("Error while uploading data file to server")
            return False


def count_rfid():
    global num, count, inputByte, inputBytes, inputByte_1, inputByte_2, inputByte_3, name, count, cnt, wg, data_list, msg, num, state, time, cnt1_list, cnt2_list, cnt3_list, cnt4_list, id_list, rssi_list, length_list
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

                ant = int(tag_id[34:36])
                rssi = tag_id[length * 2 + 4: len(tag_id)]
                msg = tag_id[36: length * 2 + 4]

                logger.debug('ID = ' + msg)
                logger.debug('Antena #' + str(ant))
                logger.debug('RSSI = ' + rssi)
                logger.debug('Length = ' + str(length))

                perm = 0
                flag = 0
                num = 0

                for i in range(len(msg_list)):
                    perm = msg in msg_list[i]
                    if perm == True:
                        num = i
                        cnt[i] = cnt[i] + 1
                        break
                if perm == False:
                    num = len(msg_list) - 1
                    msg_list[len(msg_list) - 1] = str(msg)
                    msg_list.append("")
                    cnt.append(1)

                perm = 0
                flag = 0

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
                logger.debug(len(id_list) - 1)


while True:
    if is_mode_count_rfid_and_weight():
        mode_weight = True
    if is_mode_count_rfid():
        count_rfid()
    if is_mode_send_data():
        writePARFile()
        if is_connected_to_internet() and is_server_online(STATUS_URL):
            send_data_to_server(LOAD_URL, data_list)
        else:
            logger.error("Could not connect to server")

        logger.info("System shutdown")
        os.system("sudo shutdown")
