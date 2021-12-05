#!/usr/bin/env python3
import json
import logging.config
import os
import socket
from datetime import datetime
from time import sleep, strftime

import RPi.GPIO as GPIO
import requests
import serial
import tm1637
import wiringpi
import yaml
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from models import Base, Count, Status

LOAD_URL = "http://digitalfarm.kz/loadMove"
STATUS_URL = "http://digitalfarm.kz/statusResult"
CONFIG_FILE_PATH = '/home/pi/setup.txt'

weight = 0
wgt = 0
count = 0
cnt = [0]
wg = [0]
msg_list = [""]
# buffer = 0
inputBytes = [0] * 5
name = ""
data_list = {}
tag_id = ""
msg = ""
ant = -1
rssi = ""
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
index = 0

GPIO.setmode(GPIO.BCM)

# Switch settings
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(31, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # switch 1 (BOARD 29 / BCM 5)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # switch 2 (BOARD 31 / BCM 6)

# create an engine
engine = create_engine('sqlite:///counter.sqlite')

Base.metadata.create_all(engine)

# create a configured "Session" class
Session = sessionmaker(bind=engine)

# create a Session
session = Session()


def setup_logging():
    with open('logging.yaml', 'rt') as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)


def connect_rfid(rfid_port="/dev/ttyS0"):
    rfid_counter = None
    try:
        rfid_counter = serial.Serial(rfid_port, baudrate=115200, timeout=1)
        logger.info("RFID port is ready for read: " + rfid_port)
    except serial.SerialException as ex:
        logger.error("Could not connect to RFID: " + str(ex))
    return rfid_counter


def connect_scales(weight_port1="/dev/ttyUSB0", weight_port2="/dev/ttyUSB1"):
    scales = None
    for port in [weight_port1, weight_port2]:
        try:
            scales = serial.Serial(port, baudrate=4800, parity=serial.PARITY_EVEN, timeout=1)
            # scales = serial.Serial(port, baudrate=115200, parity=serial.PARITY_EVEN, timeout=1)
        except serial.SerialException as ex:
            logger.error("Could not connect weight scales to port : " + port + ". Exception: " + str(ex))
        if scales is not None:
            return scales
    return scales


def connect_led_display():
    display = tm1637.TM1637(clk=23, dio=24)
    display.brightness(7)
    display.show('----')
    return display


def is_mode_count_rfid_and_weight():
    return GPIO.input(5) == GPIO.LOW


def is_mode_count_rfid():
    return GPIO.input(6) == GPIO.LOW


def is_mode_send_data():
    return GPIO.input(5) == GPIO.HIGH and GPIO.input(6) == GPIO.HIGH


def parse_app_config(config_path):
    logger.info("Started config parsing")
    config = {}
    with open(config_path) as f:
        for line in f:
            key, val = line.partition("=")[::2]
            config[key.strip()] = val.strip()
    logger.info("Config: " + str(config))
    logger.info("Finished config parsing")
    return config


def is_connected_to_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logger.info("Connected to internet")
        return True
    except socket.error as ex:
        logger.error("Could not connect to internet: " + ex)
        return False


def is_server_online(url):
    global name
    logger.info("[name] = " + name)
    try:
        logger.info("Sending status data")
        json_data = {
            "date": strftime("%Y-%m-%d") + ' ' + strftime("%H:%M:%S"),
            "company_code": str(name),
            "data": [
                {
                    "time": strftime("%H:%M:%S"),
                    "tag_id": "is_ready"
                }
            ]
        }
        response = requests.post(url, json=json_data)
        # Status check ex. "success\n{'company_id': 2, 'date': datetime.date(2021, 11, 2), 'time': datetime.time(22, 35, 26), 'status': 'is_ready', 'created_date': datetime.datetime(2021, 11, 2, 16, 35, 27, 936763)}"
    except IOError as ex:
        logger.error("Server status check failed " + ex)
        return False

    # logger.info("[response] status: " + str(response.status_code))
    # logger.info("[response] text: " + response.text)

    if response.status_code == requests.codes.ok:
        logger.info("Status data is sent")
    if response.text.find('success') >= 0:
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


def new_count(rfid):
    if rfid.in_waiting > 0:
        buffer = rfid.read()
        if buffer == b'\x43':
            buffer = rfid.read(2)
            if buffer.hex() == "5400":
                tag_id = "435400"
                buffer = rfid.read(1)
                data_length = int(buffer.hex(), 16)
                tag_id = tag_id + str(buffer.hex())
                buffer = rfid.read(data_length)
                tag_id = tag_id + str(buffer.hex())

                ant = int(tag_id[34:36])
                rssi = tag_id[data_length * 2 + 4: len(tag_id)]
                msg = tag_id[36: data_length * 2 + 4]
                
            
                ant1 = 1 if ant == 1 else 0
                ant2 = 1 if ant == 2 else 0
                ant3 = 1 if ant == 3 else 0
                ant4 = 1 if ant == 4 else 0

                # old one
                count_item: Count = session.query(Count).filter(
                    and_(
                        Count.tag_id == tag_id,
                        Count.status == Status.READY,
                        Count.created_date == datetime.today().strftime("%Y-%m-%d")
                    )
                ).one_or_none()

                #weight = count_weight() if is_mode_count_rfid_and_weight() else 0
                weight = 0

                if count_item is not None:
                    sum_ant = str(int(count_item.cnt) + ant1 + ant2 + ant3 + ant4)
                    count_item.update(
                        {
                            Count.rssi: rssi,
                            Count.length: data_length,
                            Count.ant1: Count.ant1 + ant1,
                            Count.ant2: Count.ant2 + ant2,
                            Count.ant3: Count.ant3 + ant3,
                            Count.ant4: Count.ant4 + ant4,
                            Count.cnt: sum_ant,
                            Count.weight: weight
                        }
                    )
                else:
                    count_item = Count(
                        company=name,
                        tag_id=tag_id,
                        length=data_length,
                        ant1=ant1,
                        ant2=ant2,
                        ant3=ant3,
                        ant4=ant4,
                        cnt=str(ant1 + ant2 + ant3 + ant4),
                        rssi=rssi,
                        weight=weight
                    )
                    session.add(count_item)

                session.commit()


def write_data_file():
    global name, count, cnt, wg, data_list, msg, index, time, cnt1_list, cnt2_list, cnt3_list, cnt4_list, id_list, rssi_list, length_list

    logger.info("Started writing data file")

    time = datetime.today()

    FILE_WRITE = '/home/pi/data/rfid_' + str(strftime("%Y-%m-%d")) + ' ' + str(strftime("%H:%M:%S")) + '.txt'

    # check file
    # first tid
    clear_file(FILE_WRITE)
    data_list = {
        "date": strftime("%Y-%m-%d"),
        "company_code": str(name),
        "data": [
            {
                "time": strftime("%H:%M:%S"),
                "tag_id": id_list[0],
                "length": length_list[0],
                "ant1": cnt1_list[0],
                "ant2": cnt2_list[0],
                "ant3": cnt3_list[0],
                "ant4": cnt4_list[0],
                "cnt": str(cnt1_list[0] + cnt2_list[0] + cnt3_list[0] + cnt4_list[0]),
                "RSSI": rssi_list[0],
                "weight": wg[0]
            }
        ]
    }
    with open(FILE_WRITE, 'w') as jf:
        json.dump(data_list, jf, indent=4)

    # other tids
    if len(id_list) - 1 > 0:
        if is_json(FILE_WRITE):
            for i in range(1, len(id_list) - 1):
                with open(FILE_WRITE) as json_file:
                    data_list = json.load(json_file)
                    new_data = {
                        "time": strftime("%H:%M:%S"),
                        "tag_id": id_list[i],
                        "length": length_list[i],
                        "ant1": cnt1_list[i],
                        "ant2": cnt2_list[i],
                        "ant3": cnt3_list[i],
                        "ant4": cnt4_list[i],
                        "cnt": str(cnt1_list[i] + cnt2_list[i] + cnt3_list[i] + cnt4_list[i]),
                        "RSSI": rssi_list[i],
                        "weight": wg[i]
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
    except IOError as ex:
        logger.error("Could not open clear file: " + str(ex))


def show(key):
    logger.debug('Write PAR File {0}'.format(key))
    if key == Key.delete:
        return False


def send_data_to_server(url, json_data):
    response = None
    try:
        logger.info("Started data file upload")
        response = requests.post(url, json=json_data)
    except IOError:
        logger.error("Could not upload data file to server")
        return False
    finally:
        # if response.text.find('success') >= 0:
        # successfull response ex. "{'status':'ok','cnt_load_str': 1}"
        # logger.info("[response] status: " + str(response.status_code))
        # logger.info("[response] text: " + response.text)
        if response.status_code == requests.codes.ok:
            logger.info("Finished data file upload")
            return True
        else:
            logger.error("Error while uploading data file to server")
            return False


def count_rfid(rfid):
    # global rfid
    global buffer, tag_id, ant, rssi, msg, index, count, msg_list, id_list, rssi_list, length_list, data_list
    global ant1_list, ant2_list, ant3_list, ant4_list
    global cnt1_list, cnt2_list, cnt3_list, cnt4_list
    global display

    # Serial READ
    if rfid.in_waiting > 0:
        buffer = rfid.read()
        if buffer == b'\x43':
            buffer = rfid.read(2)
            if buffer.hex() == "5400":
                tag_id = "435400"
                buffer = rfid.read(1)
                data_length = int(buffer.hex(), 16)
                tag_id = tag_id + str(buffer.hex())
                buffer = rfid.read(data_length)
                tag_id = tag_id + str(buffer.hex())

                ant = int(tag_id[34:36])
                rssi = tag_id[data_length * 2 + 4: len(tag_id)]
                msg = tag_id[36: data_length * 2 + 4]

                perm = 0
                index = 0

                for i in range(len(msg_list)):
                    perm = msg in msg_list[i]
                    if perm:
                        index = i
                        cnt[i] = cnt[i] + 1
                        break

                if not perm:
                    index = len(msg_list) - 1
                    msg_list[len(msg_list) - 1] = str(msg)
                    msg_list.append("")
                    cnt.append(1)
                    wg.append(0)

                perm = 0

                for i in range(len(id_list)):
                    perm = msg in id_list[i]
                    if perm:
                        index = i
                        if ant == 1:
                            cnt1_list[i] = cnt1_list[i] + 1
                        elif ant == 2:
                            cnt2_list[i] = cnt2_list[i] + 1
                        elif ant == 3:
                            cnt3_list[i] = cnt3_list[i] + 1
                        elif ant == 4:
                            cnt4_list[i] = cnt4_list[i] + 1
                        length_list[i] = data_length
                        rssi_list[i] = rssi
                        break

                if not perm:
                    index = len(id_list) - 1
                    id_list[len(id_list) - 1] = str(msg)
                    id_list.append("")
                    length_list[len(length_list) - 1] = data_length
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

                    if is_mode_count_rfid_and_weight():
                        wg[index] = count_weight()
                        # wgt = wg[i]
                        # logger.debug(wg)

                count = count + 1


def count_weight():
    global scales
    global weight, inputBytes
    perm = 1
    delay = wiringpi.millis()
    while perm:
        # perm = 1
        scales.write('E'.encode('utf-8'))
        sleep(0.001)
        error = wiringpi.millis()

        # Scales don't work. Wait 1 sec and quit with weight None
        while scales.in_waiting == 0:
            if wiringpi.millis() - error >= 1000:
                perm = 0
                weight = None
                break

        # Scales work
        if scales.in_waiting > 0 and perm:
            a = 0
            while scales.in_waiting:
                inputBytes[a] = scales.read()
                if a < 2:
                    a = a + 1
            byt = inputBytes[1] + inputBytes[0]
            byt = int.from_bytes(byt, byteorder='big')
            # precision 2 decimals
            weight = byt / 100
            if weight < 1:
                delay = wiringpi.millis()

        # TODO: 3 sec bug tag_id with weight zero-weight
        if wiringpi.millis() - delay >= 3000:
            perm = 0
    return weight


rfid = None
scales = None
display = None

setup_logging()
logger = logging.getLogger(__name__)


def main():
    global scales, rfid, display, name
    logger.info("Application started")

    config = parse_app_config(CONFIG_FILE_PATH)
    name = config["NAME"]

    if is_mode_count_rfid_and_weight():
        logger.info("Mode 1: RFID and Weight")
        rfid = connect_rfid(config["RFID_PORT"])
        scales = connect_scales(config["WEIGHT_PORT1"], config["WEIGHT_PORT2"])
        display = connect_led_display()
    elif is_mode_count_rfid():
        logger.info("Mode 2: RFID Only")
        rfid = connect_rfid()
        display = connect_led_display()
    else:
        logger.info("Mode 0: Send Data and Shutdown")

    while True:
        if is_mode_count_rfid_and_weight():
            new_count(rfid)
            # count_weight()
            if display is not None:
                display.number(len(cnt) - 1)
                pass
        elif is_mode_count_rfid():
            new_count(rfid)
            if display is not None:
                display.number(len(cnt) - 1)
        elif is_mode_send_data():
            write_data_file()
            if is_connected_to_internet() and is_server_online(STATUS_URL):
                send_data_to_server(LOAD_URL, data_list)
            else:
                logger.error("Could not connect to server")
            logger.info("System shutdown")
            os.system("sudo shutdown")
            break
        else:
            logger.error("Abnormal behavior")
            break

    # TODO: cron job to flush log file (weekly)


if __name__ == "__main__":
    main()
