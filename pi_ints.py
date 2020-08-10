# coding=utf-8
# dht_reader.py

'''
Handle pushbuttons and other interrupt devices connected to Pi.
'''

import os
import time
import RPi.GPIO as GPIO
import time

import logging
import my_logger
logger = my_logger.setup_logger(__name__,'pi_ints.log')
#dataFormat = logging.Formatter('%(levelname)s : %(message)s')
#data_logger = my_logger.setup_logger('data','pi_data.log', formatter=dataFormat)

AC_RELAY = 17
AC_ON = 19
AC_OFF = 26

# Use BCM pin mappings for Raspberry - this is most common
GPIO.setmode(GPIO.BCM)

def ac_relay_pb_callback(channel):
    print("pushbutton {}".format(channel))
    if channel==26:
        GPIO.output(23, GPIO.HIGH)
    else:
        GPIO.output(23, GPIO.LOW)


def relay_setup(relay=AC_RELAY, ron=AC_ON, roff=AC_OFF):
    print("setup {}".format(relay))
    GPIO.setup(relay, GPIO.OUT)
    # TODO: I should be able to setup with internal pullups
    GPIO.setup(ron, GPIO.IN)
    GPIO.setup(roff, GPIO.IN)
    GPIO.add_event_detect(ron, GPIO.FALLING, callback=ac_relay_pb_callback, bouncetime=300)
    GPIO.add_event_detect(roff, GPIO.FALLING, callback=ac_relay_pb_callback, bouncetime=300)

def relay_test(relay=AC_RELAY):
    print("ON {}".format(relay))
    GPIO.output(relay, GPIO.HIGH)
    time.sleep(4)
    print("OFF {}".format(relay))
    GPIO.output(relay, GPIO.LOW)

def led_setup(leds=(23,24,25)):
    for led in leds:
        print("setup {}".format(led))
        GPIO.setup(led, GPIO.OUT)

def led_test(leds=(23,24,25)):
    for led in leds:
        print("ON {}".format(led))
        GPIO.output(led, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(led, GPIO.LOW)
        time.sleep(1)

if __name__ == "__main__":
    led_setup()
    led_test()
    relay_setup()
    relay_test()
    # INFO : 2020-08-03 00:10:02,I:Geist WD100,etc.
    measure_time = time.strftime('%Y-%m-%d %H:%M:%S')
    log_str = '%s' %(measure_time)
    while True:
        time.sleep(5)
        #GPIO.output(23, GPIO.LOW)

