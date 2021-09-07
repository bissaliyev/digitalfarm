import tm1637
import RPi.GPIO as GPIO

tm = tm1637.TM1637(clk=23, dio=24)
tm.write([63, 6, 91, 79])