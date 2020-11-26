# GPIO and other interfaces used for mirror control

import RPi.GPIO as GPIO
import os
import glob
import time
import Adafruit_DHT # DHT device interface

FAKE_STATUS = False
RELAY_EN = True
AC_RELAY = 17
AC_PB_ON = 19
AC_PB_OFF = 26
RED_LED = 25
YELLOW_LED = 24
GREEN_LED = 23
DHT_TYPE=22
#DHT_PIN=5  # this is the typical default
DHT_PIN=12
DHT_RETRY_CNT=5
READ_DS18B20 = True
AUTO_ON_TIME = 30   # minutes: turn off after this time

led_map = dict(red=RED_LED, yellow=YELLOW_LED, green=GREEN_LED, grey=YELLOW_LED)

def dht_pin_setup(pin=DHT_PIN):
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def relay_setup(relay=AC_RELAY, ron=AC_PB_ON, roff=AC_PB_OFF):
    print("setup {}".format(relay))
    GPIO.setup(relay, GPIO.OUT)

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

def led_set(color, state, reset_others=True):
    if reset_others:
        for key in led_map:
            if key != color:
                GPIO.output(led_map[key], GPIO.LOW)
    GPIO.output(led_map[color], state)

def touch(path):
    ''' mimic the UNIX touch command'''
    with open(path, 'a'):
        os.utime(path, None)

# not currently used
def relay_set_with_timeout(state, override=False):
    '''
    Turn mirror heater relay on or off.
    When turned on, start a timer for 30 minutes to keep relay on.
    :param state: GPIO.HIGH or GPIO.LOW
    :param override: if True, allow override of existing state.
    '''
    if state == GPIO.HIGH or override == True:
        GPIO.output(AC_RELAY, state)
        if state == GPIO.HIGH:
            touch('/home/pi/Projects/geist_wd100/relay_on.txt')   # use file mtime to turn off after N minutes
    elif state == GPIO.LOW:
        # check timeout to see if turning off is allowed
        st = os.stat('/home/pi/Projects/geist_wd100/relay_on.txt')
        now = time.time()
        if (now - st.st_mtime) / 60 > AUTO_ON_TIME:
            GPIO.output(AC_RELAY, state)

def relay_set(state, override=False):
    '''
    Turn mirror heater relay on or off.
    Relay state can be manually overriden by pushbuttons on Pi
    :param state: GPIO.HIGH or GPIO.LOW
    :param override: if True, allow override of existing state.
    '''
    if state == GPIO.HIGH or override == True:
        GPIO.output(AC_RELAY, state)
    elif state == GPIO.LOW:
        # check timeout to see if turning off is allowed
        st = os.stat('/home/pi/Projects/geist_wd100/relay_on.txt')
        now = time.time()
        if (now - st.st_mtime) / 60 > AUTO_ON_TIME:
            GPIO.output(AC_RELAY, state)

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
    if devices:
        device_folder = devices[0]
        device_file = device_folder + '/w1_slave'
    return devices
 
def read_ds18b20_raw(dev_file):
    '''
    Fetch recent data for DS18B20
    '''
    f = open(dev_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_ds18b20(dev_file):
    '''
    Read and parse data for DS18B20.

    :return: tuple of (temp C, temp F)
    '''
    lines = read_ds18b20_raw(dev_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_ds18b20_raw(dev_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 1.8 + 32.0
        return temp_c, temp_f
    else:
        return (-100.0,-100.0)

if READ_DS18B20:
    dev_ds18b20 = ds18b20_start()   # list of devices, can be empty

def read_dht(dht_type=DHT_TYPE, dht_gpio=DHT_PIN):
    #22 is the sensor type, 5 is the GPIO pin number that DATA wire is connected to
    readOK = False
    for i in range(DHT_RETRY_CNT):
        humid, temp = Adafruit_DHT.read_retry(dht_type, dht_gpio)
        if humid and humid <= 100.0 and humid >= 0.0:
            readOK = True
            break
        # if bad reading, wait 2 seconds and try again
        time.sleep(2)
    if readOK:
        return 1.8*temp+32.0,humid
    else:
        return None,None

# How to fetch the readings that we need for heater decision
AMBIENT_T       = dict(file='geist', instrument='Geist WD100', value='temperature', name='ambient')
AMBIENT_DEW     = dict(file='geist', instrument='Geist WD100', value='dewpoint', name='ambient')
AMBIENT_HUM     = dict(file='geist', instrument='Geist WD100', value='humidity', name='ambient')
AMBIENT_T_1     = dict(file='geist', instrument='GTHD', value='temperature', name='ambient_1')
AMBIENT_DEW_1   = dict(file='geist', instrument='GTHD', value='dewpoint', name='ambient_1')
AMBIENT_HUM_1   = dict(file='geist', instrument='GTHD', value='humidity', name='ambient_1')
MIRROR_T        = dict(file='pi', instrument='ds18b20-0', value='temperature', name='mirror')
MIRROR_CELL_HUM = dict(file='pi', instrument='dht22', value='humidity', name='mirror_cell')
MIRROR_CELL_T   = dict(file='pi', instrument='dht22', value='temperature', name='mirror_cell')
#PI_DHT22_T      = dict(file='pi', instrument='dht22', value='temperature', name='pi')
#PI_DHT22_HUM    = dict(file='pi', instrument='dht22', value='humidity', name='pi')
#PI_DS18_0_T     = dict(file='pi', instrument='ds18b20-0', value='temperature', name='pi')

# ===== do not modify below this line =====
# Newest sensor readings look like this:
'''
Examples of files with latest values:
Next 2 lines from file geist_newest.dat:
2020-09-01 11:05:02,Geist WD100,temperature=68.60,humidity=60,dewpoint=54.37
2020-09-01 11:05:02,GTHD,temperature=71.36,humidity=55,dewpoint=54.36
Next 2 lines from file pi_newest.dat:
2020-09-01 11:10:02,dht22,temperature=68.4,humidity=62.4
2020-09-01 11:10:02,ds18b20-0,temperature=68.3
'''

def get_value(val, type='float'):
    '''
    Search files '*_newest.dat' for a sensor value.
    :param val: one of the items above, such as AMBIENT_T or MIRROR_CELL_DEW.
    :return: latest sensor value or None if not found.
    '''
    fp = open(val['file']+'_newest.dat', 'r')
    value = None
    for line in fp:
        if val['instrument'] in line and val['value'] in line:
            flds = line.split(',')
            for fld in flds[2:]:    # first two are not value strings
                if val['value'] in fld:
                    value = (fld.split('=')[1]).rstrip()
                    break
    if value is None or value=='n/a':
        value = -999
    else:
        if type=='float':
            value = float(value)
        elif type=='int':
            value = int(value)
    return value

def display_status():
    if stat == 'red':
        pass
    elif stat == 'yellow':
        pass
    else:
        pass
# ============================================================
# ===== Run this script from command line to test it =====
# ===== If imported to other programs, this code will not run

if __name__ == '__main__':
    for v in (AMBIENT_T,AMBIENT_DEW,AMBIENT_HUM,AMBIENT_T_1,AMBIENT_DEW_1,AMBIENT_HUM_1,MIRROR_T,MIRROR_CELL_T,MIRROR_CELL_HUM):
        val = get_value(v)
        print('name={}: instr={}, measure={}, value={}'.format(v['name'],v['instrument'],v['value'],val))
