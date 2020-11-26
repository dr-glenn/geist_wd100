# coding=utf-8
# dht_reader.py

'''
Reads DHT22 or DHT11 for temperature and humidity.
Also may read DS18B20 temp sensor.
'''

import os
import glob
import time
import math
import datetime as dt
import Adafruit_DHT # DHT device interface
import RPi.GPIO as GPIO

import logging
import my_logger
#logger = my_logger.setup_logger(__name__,'geist_prog.log')
dataFormat = logging.Formatter('%(levelname)s : %(message)s')
data_logger = my_logger.setup_logger('data','pi_data.log', formatter=dataFormat)

#from pi_hw import AC_RELAY,AC_PB_ON,AC_PB_OFF,RED_LED,YELLOW_LED,GREEN_LED,DHT_TYPE,DHT_PIN,READ_DS18B20
import pi_hw as hw

# Use BCM pin mappings for Raspberry - this is most common
GPIO.setmode(GPIO.BCM)

def f_to_c(tempF):
    return (tempF - 32.0) / 1.8
    
def c_to_f(tempC):
    return tempC * 1.8 + 32.0

def ac_relay_pb_callback(channel):
    print("pushbutton {}".format(channel))
 
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
    
def calc_dewpoint(humidity, temperatureC):
    '''
    This equation is from Geist. Strange that altitude is not in it.
    :param humidity: in percent
    :param temperatureC:
    '''
    H = (math.log(humidity / 100.0) + ((17.27 * temperatureC) / (237.3 + temperatureC))) / 17.27;
    dewptC = (237.3 * H) / (1.0 - H)
    return dewptC

def calc_status():
    '''
    green/yellow/red status depends on environmental conditions.
    '''
    if hw.FAKE_STATUS:
        dt_now = dt.datetime.now()
        # change status every 5 minutes for demonsration
        dt_min = (dt_now.minute / 5) % 3    # dt_min gets values of 0, 1 or 2
        if dt_min == 0:
            status = 'red'
        elif dt_min == 1:
            status = 'yellow'
        else:
            status = 'green'
    else:
        # TODO: should not use get_value for Pi sensors, because those values will be 5 minutes old.
        mirror_cell_t   = hw.get_value(hw.MIRROR_CELL_T)
        mirror_cell_hum = hw.get_value(hw.MIRROR_CELL_HUM)
        mirror_t        = hw.get_value(hw.MIRROR_T)  # does not have hum sensor
        # TODO: averaging is not best, esp. what if GTHD sensor is offline!
        amb_t           = (hw.get_value(hw.AMBIENT_T) + hw.get_value(hw.AMBIENT_T_1)) / 2.0
        amb_hum         = (hw.get_value(hw.AMBIENT_HUM) + hw.get_value(hw.AMBIENT_HUM_1)) / 2.0
        amb_dew         = (hw.get_value(hw.AMBIENT_DEW) + hw.get_value(hw.AMBIENT_DEW_1)) / 2.0
        if mirror_cell_hum != -999 and mirror_cell_t != -999:
            mirror_cell_dew = c_to_f(calc_dewpoint(mirror_cell_hum, f_to_c(mirror_cell_t)))
        else:
            mirror_cell_dew = -999
        # sensors return F, not C. Algorithm was specified in C, so multiply by 1.8
        if mirror_cell_dew != -999 and mirror_t != -999 and amb_hum:
            if (mirror_t - mirror_cell_dew) < (2.0 * 1.8) or amb_hum >= 80:
                status = 'red'
            elif (mirror_t - mirror_cell_dew) < (5.0 * 1.8) or amb_hum >= 65:
                status = 'yellow'
            else:
                status = 'green'
        else:
            # TODO: should be another color to signify missing sensors.
            status = 'grey'
    return status

if __name__ == "__main__":
    '''
    Read Pi sensors and write to log files.
    Calculate status, set LED color and operate heater relay.
    '''
    hw.led_setup()
    #led_test()
    hw.relay_setup()
    #relay_test()
    hw.dht_pin_setup()
    # INFO : 2020-08-03 00:10:02,I:Geist WD100,etc.
    measure_time = time.strftime('%Y-%m-%d %H:%M:%S')

    if hw.READ_DS18B20:
        dev_ds18b20 = hw.ds18b20_start()   # list of devices, can be empty
        if not dev_ds18b20:
            data_logger.error(measure_time + ': DS18B20 device not found')

    log_str = '%s' %(measure_time)
    instruments = {}

    # DHT22 temp/humidity - only one
    temp,humid = hw.read_dht()
    if humid:   # bad read returns humid=None
        instruments['dht22'] = {'temperature':'{:.1f}'.format(temp), 'humidity':'{:.1f}'.format(humid)}
    else:
        instruments['dht22'] = {'temperature':'n/a', 'humidity':'n/a'}
        data_logger.error(measure_time + ': DHT22: no readings')

    # DS18B20 temp sensors - can have multiple
    if hw.READ_DS18B20:
        idev = 0
        if dev_ds18b20:
            for dev in dev_ds18b20:
                ds_temp_c,ds_temp_f = hw.read_ds18b20(dev+'/w1_slave')
                instruments['ds18b20-%d' %(idev)] = {'temperature':'{:.1f}'.format(ds_temp_f)}
                idev += 1

    if humid and temp:
        mirror_cell_dew = c_to_f(calc_dewpoint(humid,f_to_c(temp)))
        instruments['dew_calc'] = {'mirror_dewpt':'{:.1f}'.format(mirror_cell_dew)}
    else:
        instruments['dew_calc'] = {'mirror_dewpt':'n/a'}
    
    # environment calc_status returns one of: red/yellow/green
    stat = calc_status()
    # set the heater relay and the status LED
    #if not hw.FAKE_STATUS:
    if hw.RELAY_EN:
        if stat == 'red':
            hw.relay_set(GPIO.HIGH)
        else:
            hw.relay_set(GPIO.LOW)
    hw.led_set(stat, GPIO.HIGH) # by default other LEDs will be turned off
    instruments['environment'] = {'status': stat}

    # read mirror heater relay (even though we just set it above here)
    rstate = 'ON' if GPIO.input(hw.AC_RELAY) else 'Off'
    instruments['relay'] = {'state': '%s' %(rstate)}

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

