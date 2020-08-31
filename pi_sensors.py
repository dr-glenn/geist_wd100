# coding=utf-8
# dht_reader.py

'''
Reads DHT22 or DHT11 for temperature and humidity.
Also may read DS18B20 temp sensor.
'''

import os
import glob
import time
import datetime as dt
import Adafruit_DHT # DHT device interface
import RPi.GPIO as GPIO

import logging
import my_logger
#logger = my_logger.setup_logger(__name__,'geist_prog.log')
dataFormat = logging.Formatter('%(levelname)s : %(message)s')
data_logger = my_logger.setup_logger('data','pi_data.log', formatter=dataFormat)

from pi_hw import AC_RELAY,AC_PB_ON,AC_PB_OFF,RED_LED,YELLOW_LED,GREEN_LED,DHT_TYPE,DHT_PIN,READ_DS18B20
'''
AC_RELAY = 17
AC_PB_ON = 19
AC_PB_OFF = 26
RED_LED = 25
YELLOW_LED = 24
GREEN_LED = 23
DHT_TYPE=22
DHT_PIN=5
READ_DS18B20 = True
'''

# Use BCM pin mappings for Raspberry - this is most common
GPIO.setmode(GPIO.BCM)

def ac_relay_pb_callback(channel):
    print("pushbutton {}".format(channel))

def relay_setup(relay=AC_RELAY, ron=AC_PB_ON, roff=AC_PB_OFF):
    print("setup {}".format(relay))
    GPIO.setup(relay, GPIO.OUT)
    # AC_PB are used in pi_ints.py, do not setup here!
    #GPIO.setup(ron, GPIO.IN)
    #GPIO.setup(roff, GPIO.IN)
    #GPIO.add_event_detect(ron, GPIO.FALLING, callback=ac_relay_pb_callback, bouncetime=300)
    #GPIO.add_event_detect(roff, GPIO.FALLING, callback=ac_relay_pb_callback, bouncetime=300)

def relay_test(relay=AC_RELAY):
    print("ON {}".format(relay))
    GPIO.output(relay, GPIO.HIGH)
    time.sleep(4)
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

def ds18b20_start():
    '''
    Setup for reading DS18B20.
    It is a system device on r-pi and leaves data in /sys/bus...
    There can be multiple - each has its own directory.

    :return: filenames for device data
    '''
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
 
    base_dir = '/sys/bus/w1/devices/'
    devices = glob.glob(base_dir + '28*')
    # next 2 lines show you how to access a single DS18B20
    device_folder = devices[0]
    device_file = device_folder + '/w1_slave'
    return devices
 
def read_temp_raw(dev_file):
    '''
    Fetch recent data for DS18B20
    '''
    f = open(dev_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp(dev_file):
    '''
    Read and parse data for DS18B20.

    :return: tuple of (temp C, temp F)
    '''
    lines = read_temp_raw(dev_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(dev_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f
    else:
        return (-100.0,-100.0)

if READ_DS18B20:
    dev_ds18b20 = ds18b20_start()

def read_dht(dht_type=DHT_TYPE, dht_gpio=DHT_PIN):
    #22 is the sensor type, 5 is the GPIO pin number that DATA wire is connected to
    humid, temp = Adafruit_DHT.read_retry(dht_type, dht_gpio)
    return 1.8*temp+32.0,humid

def calc_status():
    '''
    green/yellow/red status depends on environmental conditions.
    '''
    dt_now = dt.datetime.now()
    # change status every 5 minutes for demonsration
    dt_min = (dt_now.minute / 5) % 3
    if dt_min == 0:
        status = 'red'
    elif dt_min == 1:
        status = 'yellow'
    else:
        status = 'green'
    return status

if __name__ == "__main__":
    led_setup()
    #led_test()
    relay_setup()
    #relay_test()
    # INFO : 2020-08-03 00:10:02,I:Geist WD100,etc.
    measure_time = time.strftime('%Y-%m-%d %H:%M:%S')
    log_str = '%s' %(measure_time)
    instruments = {}

    # DHT22 temp/humidity - only one
    temp,humid = read_dht()
    print("temp={:.1f}, humidity={:.1f}".format(temp,humid))
    instruments['dht22'] = {'temperature':'{:.1f}'.format(temp), 'humidity':'{:.1f}'.format(humid)}

    # mirror heater relay
    rstate = 'ON' if GPIO.input(AC_RELAY) else 'Off'
    instruments['relay'] = {'state': '%s' %(rstate)}

    stat = calc_status()
    instruments['environment'] = {'status': stat}

    # DS18B20 temp sensors - can have multiple
    if READ_DS18B20:
        idev = 0
        for dev in dev_ds18b20:
            ds_temp_c,ds_temp_f = read_temp(dev+'/w1_slave')
            instruments['ds18b20-%d' %(idev)] = {'temperature':'{:.1f}'.format(ds_temp_f)}
            idev += 1

    # write sensors to log file
    for instr in instruments:
        log_str += ',I:%s' %(instr)
        data = instruments[instr]
        for key in data:
            log_str += ',V:%s,%s' %(key,data[key])
    data_logger.info(log_str)

    # write sensors to newest file, one value per line
    fp = open('pi_newest.dat', 'w')
    for instr in instruments:
        log_str = '%s' %(measure_time)
        log_str += ',%s' %(instr)
        fp.write(log_str)
        data = instruments[instr]
        for key in data:
            dat_str = ',%s=%s' %(key,data[key])
            fp.write(dat_str)
        fp.write('\n')
    fp.close()

