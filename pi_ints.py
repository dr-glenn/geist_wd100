# coding=utf-8
# dht_reader.py

'''
Handle pushbuttons and other interrupt devices connected to Pi.
If relay is manually turned on by pushbutton, then it starts a timer (30 minutes?).
When timer expires, then relay will turn off.
If sensors require the relay on, they will turn it on again within 5 minutes.

When program starts, the red LED on the Pi will flash and the relay will be turned on for 2 seconds.
'''

import os
import os.path
import time
import RPi.GPIO as GPIO

import logging
import my_logger
logger = my_logger.setup_logger(__name__,'pi_ints.log')
#dataFormat = logging.Formatter('%(levelname)s : %(message)s')
#data_logger = my_logger.setup_logger('data','pi_data.log', formatter=dataFormat)

# I cannot run this program as a cron job if attempting to import pi_hw.
# The problem is that pi_hw import Adafruit_DHT and for some reason the cron job can't fetch it.
# So Ihave to replicate the hardware pin assignments here.
#from pi_hw import AC_RELAY,AC_PB_ON,AC_PB_OFF,RED_LED,YELLOW_LED,GREEN_LED
RELAY_EN = True
AC_RELAY = 17
AC_PB_ON = 19
AC_PB_OFF = 26
RED_LED = 25
YELLOW_LED = 24
GREEN_LED = 23
AUTO_ON_TIME = 30   # minutes: turn off after this time
AUTO_OFF_TIME = 15  # minutes required to stay off

# Two files used for operator manual control of heater
RELAY_ON_FILE  = '/home/pi/relay_on.txt'
RELAY_OFF_FILE = '/home/pi/relay_off.txt'

# Use BCM pin mappings for Raspberry - this is most common
GPIO.setmode(GPIO.BCM)

def ac_relay_pb_callback(channel):
    '''
    button pushes by interrupt handler.
    :param channel: GPIO pin of the pushbutton
    '''
    global on_timer, on_manual
    #print("pushbutton {}".format(channel))
    logger.info("heater relay manual: %s" %("ON" if channel==AC_PB_ON else "OFF"))
    if channel==AC_PB_ON:
        #GPIO.output(AC_RELAY, GPIO.HIGH)
        #GPIO.output(RED_LED, GPIO.HIGH)
        on_timer = AUTO_ON_TIME
        on_manual = True
        os.system('touch '+RELAY_ON_FILE)   # use file timestamp for the relay ON timer
    else:
        #GPIO.output(AC_RELAY, GPIO.LOW)
        #GPIO.output(RED_LED, GPIO.LOW)
        on_timer = 0
        on_manual = True
        os.remove(RELAY_ON_FILE)
        os.system('touch '+RELAY_OFF_FILE)   # use file timestamp for the relay ON timer

def relay_setup(relay=AC_RELAY, ron=AC_PB_ON, roff=AC_PB_OFF):
    GPIO.setup(relay, GPIO.OUT)
    # TODO: I should be able to setup with internal pullups
    GPIO.setup(ron, GPIO.IN)
    GPIO.setup(roff, GPIO.IN)
    GPIO.add_event_detect(ron, GPIO.FALLING, callback=ac_relay_pb_callback, bouncetime=300)
    GPIO.add_event_detect(roff, GPIO.FALLING, callback=ac_relay_pb_callback, bouncetime=300)

def relay_test(relay=AC_RELAY):
    print("ON {}".format(relay))
    GPIO.output(relay, GPIO.HIGH)
    time.sleep(2)
    print("OFF {}".format(relay))
    GPIO.output(relay, GPIO.LOW)

def led_setup(leds=(GREEN_LED,YELLOW_LED,RED_LED)):
    for led in leds:
        print("setup {}".format(led))
        GPIO.setup(led, GPIO.OUT)

def led_test(leds=(GREEN_LED,YELLOW_LED,RED_LED)):
    for led in leds:
        print("ON {}".format(led))
        GPIO.output(led, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(led, GPIO.LOW)
        time.sleep(1)

# This function is only used if we want to enforce limits to time on and time off for the heater.
# NOT currently used (1 Feb 2021), and not currently correct!
def relay_control_with_timeout():
    # Also need to be able to manually control relay from desktop console.
    relay_on = False
    if os.path.exists(RELAY_ON_FILE):
        st_relay_on = os.stat(RELAY_ON_FILE)
        now = time.time()
        if (now - st_relay_on.st_mtime) / 60 > AUTO_ON_TIME:
            # relay is ON, we want to turn off and set OFF timer so that relay cannot
            # be turned on too soon
            relay_on = False
            os.remove(RELAY_ON_FILE)
            os.system('touch '+RELAY_OFF_FILE)
        else:
            # less than AUTO_ON_TIME, so makes sure relay is ON
            relay_on = True
    if os.path.exists(RELAY_OFF_FILE):
        st_relay_off = os.stat(RELAY_OFF_FILE)
        now = time.time()
        if (now - st_relay_off.st_mtime) / 60 < AUTO_OFF_TIME:
            # heater must stay off
            relay_on = False
            os.remove(RELAY_ON_FILE)
        else:
            # greater than AUTO_OFF_TIME, so allow relay to turn on
            os.remove(RELAY_OFF_FILE)
    if relay_on:
        GPIO.output(AC_RELAY, GPIO.HIGH)
        GPIO.output(RED_LED, GPIO.HIGH)
    else:
        GPIO.output(AC_RELAY, GPIO.LOW)
        GPIO.output(RED_LED, GPIO.LOW)

if __name__ == "__main__":
    global on_timer, on_manual
    logger.info('START pi_ints')
    on_timer = 0
    on_manual = False
    led_setup()
    led_test()
    relay_setup()
    relay_test()
    # INFO : 2020-08-03 00:10:02,I:Geist WD100,etc.
    measure_time = time.strftime('%Y-%m-%d %H:%M:%S')
    log_str = '%s' %(measure_time)
    while True:
        # We have to run infinite loop just to keep this program running,
        # but nothing is actually done here, it's all handled by interrupts.
        
        # on_manual is True if a hardware pushbutton was activated
        relay_on = False
        if os.path.exists(RELAY_ON_FILE):
            on_manual = True
            # it was turned on manually, either pushbutton or console command
            st_relay_on = os.stat(RELAY_ON_FILE)
            now = time.time()
            if (now - st_relay_on.st_mtime) / 60 > AUTO_ON_TIME:
                # relay is ON, we want to turn off and set OFF timer so that relay cannot
                # be turned on too soon
                relay_on = False
                os.remove(RELAY_ON_FILE)
                on_manual = False
            else:
                # less than AUTO_ON_TIME, so makes sure relay is ON
                relay_on = True
        if os.path.exists(RELAY_OFF_FILE):
            on_manual = True    # manually turned off, same flag for ON state
            st_relay_off = os.stat(RELAY_OFF_FILE)
            now = time.time()
            if (now - st_relay_off.st_mtime) / 60 > AUTO_OFF_TIME:
                # greater than AUTO_OFF_TIME, so allow relay to turn on
                os.remove(RELAY_OFF_FILE)
                on_manual = False
            else:
                # heater must stay off
                relay_on = False
                os.remove(RELAY_ON_FILE)
        if on_manual:   # don't change relay if under automatic control
            if relay_on:
                GPIO.output(AC_RELAY, GPIO.HIGH)
                GPIO.output(RED_LED, GPIO.HIGH)
            else:
                GPIO.output(AC_RELAY, GPIO.LOW)
                GPIO.output(RED_LED, GPIO.LOW)
        time.sleep(30)

