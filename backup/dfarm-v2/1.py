import tm1637
tm = tm1637.TM1637(clk=23, dio=24)
# all LEDS on "88:88"
#tm.write([127, 255, 127, 127])
# show "HELP"
tm.show('----')
#tm.temperature(24)