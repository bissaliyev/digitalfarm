import tm1637
import time
import datetime
import RPi.GPIO as GPIO
import sys

# Simply change the CLK and DIO pin numbers of 23 and 24 to match the Pi GPIO pins you've used.
Display = tm1637.TM1637(16, 18, tm1637.BRIGHT_TYPICAL)

Display.SetBrightnes(1)


while True:
    now =datetime.datetime.now()
#    print(now)
    hour=now.hour
    minute=now.minute
    second=now.second
    currenttime=[int(hour/10), hour%10, int(minute/10), minute %10]
#    print(currenttime)
    Display.Show(currenttime)
    Display.ShowDoublepoint(second % 2)
    
    time.sleep(1)
        

#display.Clear()
#GPIO.cleanup()