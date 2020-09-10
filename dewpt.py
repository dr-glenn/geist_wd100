# calc dewpoint based on T and H
import math


def f_to_c(tempF):
    return (tempF - 32.0) / 1.8

def c_to_f(tempC):
    return tempC * 1.8 + 32.0
    
def calc_dewpoint(humidity, temperatureC):
    '''
    This equation is from Geist. Strange that altitude is not in it.
    :param humidity: in percent
    :param temperatureC:
    '''
    H = (math.log(humidity / 100.0) + ((17.27 * temperatureC) / (237.3 + temperatureC))) / 17.27;
    dewptC = (237.3 * H) / (1.0 - H)
    return dewptC

    
def calc_dewpoint10(humidity, temperatureC):
    '''
    This equation is from Geist. Strange that altitude is not in it.
    :param humidity: in percent
    :param temperatureC:
    '''
    H = (math.log10(humidity / 100.0) + ((17.27 * temperatureC) / (237.3 + temperatureC))) / 17.27;
    dewptC = (237.3 * H) / (1.0 - H)
    return dewptC

humid=80
tempF = 50
tempC = f_to_c(tempF)
print('tempC={:.1f}'.format(tempC))
print('log_e: dewpt={:.1f}, T={}, H={}'.format(c_to_f(calc_dewpoint(humid,tempC)),tempF,humid))
print('log10: dewpt={:.1f}, T={}, H={}'.format(c_to_f(calc_dewpoint10(humid,tempC)),tempF,humid))
