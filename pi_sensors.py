# coding=utf-8
# dht_reader.py

'''
Reads DHT22 or DHT11 for temperature and humidity.
Also may read DS18B20 temp sensor.
'''

import os
import glob
import time
import Adafruit_DHT # DHT device interface
import RPi.GPIO as GPIO
import time

import logging
import my_logger
#logger = my_logger.setup_logger(__name__,'geist_prog.log')
dataFormat = logging.Formatter('%(levelname)s : %(message)s')
data_logger = my_logger.setup_logger('data','pi_data.log', formatter=dataFormat)

AC_RELAY = 17
READ_DS18B20 = False
DHT_TYPE=22
DHT_PIN=5

# Use BCM pin mappings for Raspberry - this is most common
GPIO.setmode(GPIO.BCM)

def relay_setup(relay=AC_RELAY):
    print("setup {}".format(relay))
    GPIO.setup(relay, GPIO.OUT)

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

def ds18b20_start():
    '''
    Setup for reading DS18B20.
    It is a system device on r-pi and leaves data in /sys/bus...

    :return: filename for device data
    '''
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
 
    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
    return device_file
 
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

if __name__ == "__main__":
    led_setup()
    led_test()
    #relay_setup()
    #relay_test()
    # INFO : 2020-08-03 00:10:02,I:Geist WD100,etc.
    measure_time = time.strftime('%Y-%m-%d %H:%M:%S')
    log_str = '%s' %(measure_time)
    instruments = {}
    temp,humid = read_dht()
    print("temp={:.1f}, humidity={:.1f}".format(temp,humid))
    instruments['dht22'] = {'temperature':'{:.1f}'.format(temp), 'humidity':'{:.1f}'.format(humid)}

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

