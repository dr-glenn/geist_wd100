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
dataFormat = logging.Formatter('%(levelname)s : %(message)s')
data_logger = my_logger.setup_logger('data','pi_data.log', formatter=dataFormat)
data_logger.setLevel(logging.DEBUG)

#from pi_hw import AC_RELAY,AC_PB_ON,AC_PB_OFF,RED_LED,YELLOW_LED,GREEN_LED,DHT_TYPE,DHT_PIN,READ_DS18B20
import pi_hw as hw

hw.set_logger(data_logger)

MIRROR_STAT = {0:'grey', 1:'green', 2:'yellow', 3:'red'}

# Use BCM pin mappings for Raspberry - this is most common
GPIO.setmode(GPIO.BCM)

def f_to_c(tempF):
    return (tempF - 32.0) / 1.8
    
def c_to_f(tempC):
    return tempC * 1.8 + 32.0

def ac_relay_pb_callback(channel):
    print("pushbutton {}".format(channel))
    
def calc_dewpoint(humidity, temperatureC):
    '''
    This equation is from Geist. Strange that altitude is not in it.
    :param humidity: in percent
    :param temperatureC:
    '''
    H = (math.log(humidity / 100.0) + ((17.27 * temperatureC) / (237.3 + temperatureC))) / 17.27;
    dewptC = (237.3 * H) / (1.0 - H)
    return dewptC

def calc_status(mirror_cell_t, mirror_t, mirror_cell_hum):
    '''
    green/yellow/red status depends on environmental conditions.
    This function also calculates status based on Geist sensors.
    :param mirror_cell_t: temperature measured in the mirrir cell
    :param mirror_t: temperature measured on the mirror
    :mirror_cell_hum: humidity in the mirror cell
    :return: list of status values for each of Geist, GTHD, Pi sensors
    '''
    def calc_color(temp, dewtemp, humid):
        """
        If any of the values are missing, then return color grey.
        """
        if temp == hw.MISSING_VAL or dewtemp == hw.MISSING_VAL or humid == hw.MISSING_VAL:
            status = 'grey'
            istatus = 0
        else:
            if (temp - dewtemp) < 2.0 or humid >= 80:
                status = 'red'
                istatus = 3
            elif (temp - dewtemp) < 5.0 or humid >= 65:
                status = 'yellow'
                istatus = 2
            else:
                status = 'green'
                istatus = 1
        return istatus

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
        stat_list = []
        # Next 3 are pi sensors, get live values
        """
        vals = hw.get_all_sensors()
        mirror_cell_t = vals['PI_DHT_T']
        mirror_cell_hum = vals['PI_DHT_H']
        mirror_t = vals['PI_DS18_T']
        """
        if mirror_cell_hum != hw.MISSING_VAL and mirror_cell_t != hw.MISSING_VAL:
            mirror_cell_dew = calc_dewpoint(mirror_cell_hum, mirror_cell_t)
        else:
            mirror_cell_dew = hw.MISSING_VAL
        istat = calc_color(mirror_t, mirror_cell_dew, mirror_cell_hum)
        stat_list.append(istat)
        stat = MIRROR_STAT[istat]
        data_logger.debug('pi status: %s, vals: %.1f, %.1f, %.1f' %(stat, mirror_t, mirror_cell_dew, mirror_cell_hum))
        # The next measurements are from Geist and we fetch from a file of recently stored values
        amb_t   = hw.get_value(hw.AMBIENT_T)
        amb_hum = hw.get_value(hw.AMBIENT_HUM)
        amb_dew = hw.get_value(hw.AMBIENT_DEW)
        istat = calc_color(amb_t, amb_dew, amb_hum)
        stat_list.append(istat)
        stat = MIRROR_STAT[istat]
        data_logger.debug('G100 status: %s' %(stat))

        amb_t   = hw.get_value(hw.AMBIENT_T_1)
        amb_hum = hw.get_value(hw.AMBIENT_HUM_1)
        amb_dew = hw.get_value(hw.AMBIENT_DEW_1)
        istat = calc_color(amb_t, amb_dew, amb_hum)
        stat_list.append(istat)
        stat = MIRROR_STAT[istat]
        data_logger.debug('GTHD status: %s' %(stat))

        status = max(stat_list)
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

    # DS18B20 temp sensors - can have multiple
    ds_temp = []
    if hw.READ_DS18B20:
        idev = 0
        if dev_ds18b20:
            for dev in dev_ds18b20:
                ds_temp_c = hw.read_ds18b20(dev+'/w1_slave')
                ds_temp.append(ds_temp_c)
                instruments['ds18b20-%d' %(idev)] = {'temperature':'{:.1f}'.format(ds_temp_c)}
                idev += 1
        else:   # there is no ds18b20, but we want to keep a placeholder
            ds_temp.append(hw.MISSING_VAL)
            instruments['ds18b20-%d' %(idev)] = {'temperature':'n/a'}
            

    # DHT22 temp/humidity - only one
    tempc,humid = hw.read_dht()
    if humid != hw.MISSING_VAL and tempc != hw.MISSING_VAL:   # bad read returns humid=None
        instruments['dht22'] = {'temperature':'{:.1f}'.format(tempc), 'humidity':'{:.1f}'.format(humid)}
        mirror_cell_dew = calc_dewpoint(humid,tempc)
        instruments['dew_calc'] = {'mirror_dewpt':'{:.1f}'.format(mirror_cell_dew)}
    else:
        humid = hw.MISSING_VAL
        tempc = hw.MISSING_VAL
        instruments['dht22'] = {'temperature':'n/a', 'humidity':'n/a'}
        mirror_cell_dew = hw.MISSING_VAL
        instruments['dew_calc'] = {'mirror_dewpt':'n/a'}
        data_logger.error(measure_time + ': DHT22: no readings')
    
    # environment calc_status returns one of: red/yellow/green/grey as integer
    istat = calc_status(tempc, ds_temp[0], humid)
    stat = MIRROR_STAT[istat]
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

