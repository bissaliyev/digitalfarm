import subprocess
from time import sleep
import RPi.GPIO as GPIO
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

fileHandler = logging.FileHandler("/home/pi/autostart.log")
fileHandler.setFormatter(logFormatter)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

GPIO.setmode(GPIO.BOARD)

GPIO.setup(29, GPIO.IN)
GPIO.setup(31, GPIO.IN)

program_cmd_1 = 'python3 /home/pi/seriaql_test_dev_weight.py'
program_cmd_2 = 'python3 /home/pi/seriaql_test_dev_everyday.py'

is_running_1 = False
is_running_2 = False

# for running subprocess
def execute(cmd):
    os.system(cmd)

# main loop
sleep(5)

logger.info('Start')

while True:
    if (GPIO.input(29) == True) and (not is_running_1):
        sleep(5)
        logger.info('First')
        logger.info("Weight")
        is_running_1 = True
        is_running_2 = False
        execute(program_cmd_1)
        
    if(GPIO.input(31) == True) and (not is_running_2):
        sleep(5)
        logger.info('Second')
        logger.info("Everyday")
        is_running_1 = False
        is_running_2 = True
        execute(program_cmd_2)
       

    sleep(0.2)