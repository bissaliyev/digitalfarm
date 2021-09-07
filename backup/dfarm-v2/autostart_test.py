import RPi.GPIO as GPIO
import os

GPIO.setmode(GPIO.BOARD)

GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(31, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print('Check PINs')

if GPIO.input(29) == GPIO.LOW:
    print('First')
if GPIO.input(31) == GPIO.HIGH:
    print('Second')

