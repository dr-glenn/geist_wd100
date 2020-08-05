#!/usr/bin/env python
# Read environmental data from Geist Watchdog 100
# Geist provides a HTTP API that returns data as JSON.
# This program extracts temperature, humidity and dew point temperature from JSON.
# It generates either printed output to the console or HTML to be displayed in a web browser.

"""
Conrolling telescope mirror heaters.
This program will run continuously and is launched at boot time.
It also needs to be checked by a cron job in case it goes down.
The program will query the Geist WD100 every few minutes for environment: temp, humidity, dew point.
The program maintains a list of recent values that can be queried by a web application.
It should also write the values to log files in case the program goes down.
When critical conditions are encountered (dew point and mirror temp close in values),
the mirror heater should be turned on, and a notiiication sent out.

The conditions that turn on the heater can be set from a web application and are stored in a config file.
"""
# Apache in Centos 7 uses Python 2.7.
# Python 2.7 does not have urllib.request
import urllib.request      # Python 3.4+
#import urllib
import json
import os
import smtplib,ssl
from email.message import EmailMessage

TEST_EMAIL = False

if os.path.isfile('pi_settings.py'):
    import pi_settings as gset
    dewpoint_alarm = gset.dewpoint_alarm
    dewpoint_temp = gset.dewpoint_temp
    mirror_temp = gset.mirror_temp
    geist_addr = gset.geist_addr
    geist_port = gset.geist_port
    email_acct = None
else:
    dewpoint_alarm = 4.0    # diff between ambient dewpoint and mirror temperature in F
    dewpoint_temp = ('Geist WD100','dewpoint')
    mirror_temp = ('GTHD','temperature')
    geist_addr = 'http://198.189.159.214'   # address of geist Watchdog
    geist_port = 89     # use None for default port value
    email_acct = 'developer@glenn-nelson.us'
    email_acct_pass = 'PxTMn}.=@ORu'
    email_from = 'developer@glenn-nelson.us'
    email_to = 'kitecamguy@gmail.com'

import logging
import my_logger
logger = my_logger.setup_logger(__name__,'geist_prog.log')
dataFormat = logging.Formatter('%(levelname)s : %(message)s')
data_logger = my_logger.setup_logger('data','geist_data.log', formatter=dataFormat)

def get_path_entity(dataDict,path):
    """
    Search the dataDict (JSON returned from Geist) for nodes that match the path.
    :param dataDict: JSON as a nested dictionary obtained from Geist query
    :param path: tuple or list of node names in dataDict to find
    :return: list of nodes that match path
    path parameter can designate nodes by single name or by tuple of names or by '*'.
    For example, we search for path = ('data', '*', 'entity', '0'). This will match
    the toplevel node named 'data', then all nodes within 'data', then all nodes in
    those matches that are named 'entity', and finally nodes named '0'.
    """
    nodes = []
    nnodes = None
    node = dataDict
    for index,p in enumerate(path):
        if p == '*':
            # recurse over all nodes in current node
            nnodes = []
            logger.debug('p = *, handle %s' %(str(path[index+1:])))
            logger.debug('node = %s' %(str(node)))
            for n in node:
                logger.debug('n = %s' %(str(n)))
                nnode = get_path_entity(node[n],path[index+1:])
                logger.debug('nnode = %s' % (str(nnode)))
                nnodes.extend(nnode)
            break
        elif isinstance(p,(tuple,list)):
            nnodes = []
            for n in node:
                if n in p:
                    nnode = get_path_entity(node[n],path[index+1:])
                    nnodes.extend(nnode)
        else:
            logger.debug('index = %d, p = %s, node = %s' %(index,p,str(node)))
            logger.debug('p = %s, node[p] = %s' %(p,str(node[p])))
            node = node[p]
    if nnodes:
        nodes.extend(nnodes)
    else:
        nodes.append(node)  # TODO: should this be extend instead of append?
    return nodes

def get_geist_data(theURL, query):
    """
    Get JSON from Geist.
    :param theURL: device address
    :param query: query string according to Geist API
    :return: JSON
    """
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36'
    # req = urllib.request.Request(theURL+query, headers={'User-Agent':user_agent})
    # req = urllib.request.Request(theURL + query)
    opener = urllib.request.urlopen(theURL + query)
    html = opener.read().decode('utf-8')
    logger.debug('json size = %d' %(len(html)))
    jdata = json.loads(html)
    return jdata

def html_out(geist_state, geist_data):
    # write html page
    """
    Using data parsed from the JSON, generate web page.
    :param geist_stateL state data includes device timestamp
    :param geist_data: JSON returned by Geist /api/dev
    """
    print('Content-Type: text/html;charset=utf-8\n')
    print('<!DOCTYPE html>')
    out0 = """
<html>
<head>
<title>Geist Environment Data</title>
</head>
<body>
<H1>Geist Enviroment</H1>
<H2>Date: %s</H2>
    """
    out1 = """
</body>
</html>
    """
    gpath = ('data', '*', 'entity', '0')
    nodes = get_path_entity(geist_data, gpath)
    instrument = {}
    for node in nodes:
        # Only process nodes that match specific device names
        if 'name' in node and node['name'] in measure_src:
            # Get all nodes within a node named 'measurement'
            meas_nodes = get_path_entity(node, ('measurement',))
            #print('name=%s' % (node['name']))
            instrument[node['name']] = {}
            measures = {}
            for items in meas_nodes:
                for key in items:
                    #print('key=%s, type=%s, value=%s' % (key,items[key]['type'], items[key]['value']))
                    measures[key] = [items[key]['type'], items[key]['value']]
            instrument[node['name']] = measures

    out = out0 %(geist_state['data']['localTime'])
    for instr in instrument:
        instr_str = '<H3>%s</H3>' %(instr)
        measures = instrument[instr]
        for key in measures:
            instr_str += '<p>%s: %s %s</p>' %(key,measures[key][0],measures[key][1])
        out += instr_str
    out += out1
    print(out)  # sends HTML to HTTP stream


def log_data(geist_state, geist_data):
    # write html page
    global measure_src, gpath
    """
    Using data parsed from the JSON, generate web page.
    :param geist_stateL state data includes device timestamp
    :param geist_data: JSON returned by Geist /api/dev
    """
    gpath = ('data', '*', 'entity', '0')
    nodes = get_path_entity(geist_data, gpath)
    instruments = {}
    for node in nodes:
        # Only process nodes that match specific device names
        if 'name' in node and node['name'] in measure_src:
            # Get all nodes within a node named 'measurement'
            meas_nodes = get_path_entity(node, ('measurement',))
            #print('name=%s' % (node['name']))
            instruments[node['name']] = {}
            measures = {}
            for items in meas_nodes:
                for key in items:
                    #print('key=%s, type=%s, value=%s' % (key,items[key]['type'], items[key]['value']))
                    measures[key] = [items[key]['type'], items[key]['value']]
            instruments[node['name']] = measures

    measure_time = geist_state['data']['localTime']
    log_str = '%s' %(measure_time)
    measures = {}
    for instr in instruments:
        #instr_str = '<H3>%s</H3>' %(instr)
        log_str += ',I:%s' %(instr)
        measures[instr] = {}
        data = instruments[instr]
        for key in data:
            log_str += ',V:%s,%s' %(data[key][0],data[key][1])
            measures[instr][data[key][0]] = data[key][1]
    data_logger.info(log_str)

    # write sensors to newest file, one value per line
    fp = open('geist_newest.dat', 'w')
    for instr in instruments:
        log_str = '%s' %(measure_time)
        log_str += ',%s' %(instr)
        fp.write(log_str)
        data = instruments[instr]
        for key in data:
            dat_str =',%s=%s' %(data[key][0],data[key][1])
            fp.write(dat_str)
        fp.write('\n')
    fp.close()

    return measure_time,measures

def send_email():
    port = 465
    context = ssl.create_default_context()
    msg = EmailMessage()
    msg.set_content('geist_pi says hello')
    msg['Subject'] = 'Geist'
    msg['From'] = email_from
    msg['To'] = email_to
    with smtplib.SMTP_SSL('mail.glenn-nelson.us', port, context) as server:
        server.login(email_acct, email_acct_pass)
        server.sendmail(email_from, email_to, msg.as_string())

if __name__ == '__main__':
    logger.info('Geist fetch start')
    #gpath = ('data', '740491621DC31CC3', 'entity', '0')
    #gpath = ('data', '*', 'entity', '0', 'measurement')
    # traverse JSON nested dicts: "data/*/entity/0"
    gpath = ('data', '*', 'entity', '0')
    # Look for dict nodes tha match these data sources:
    measure_src = ['Geist WD100', 'GTHD']
    theURL = geist_addr
    if geist_port:
        theURL += ':' + str(geist_port)

    # query to get the local time
    query = '/api/sys/state?cmd=get'
    geist_state = get_geist_data(theURL, query)
    logger.debug('geist_state = %s' %(str(geist_state)))
    logger.info('Datetime: %s' %(geist_state['data']['localTime']))

    # query to get all the data
    query = '/api/dev?cmd=get'
    geist_json = get_geist_data(theURL, query)
    # Find matching nodes: use gdata for local test, geist_json for live data
    nodes = get_path_entity(geist_json, gpath)
    """
    # Everything here is just for debugging
    #logger.debug(nodes)
    for node in nodes:
        # Only process nodes that match specific device names
        if 'name' in node and node['name'] in measure_src:
            # Get all nodes within a node named 'measurement'
            meas_nodes = get_path_entity(node, ('measurement',))
            logger.debug('name=%s' % (node['name']))
            for items in meas_nodes:
                for key in items:
                    logger.debug('key=%s, type=%s, value=%s' % (key,items[key]['type'], items[key]['value']))
    """

    measure_time,measures = log_data(geist_state,geist_json)
    Tdewpoint = measures[dewpoint_temp[0]][dewpoint_temp[1]]
    Tmirror   = measures[mirror_temp[0]][mirror_temp[1]]
    logger.info('ambient dewpoint=%s, mirror temp=%s' %(Tdewpoint,Tmirror))
    if TEST_EMAIL or float(Tmirror) - float(Tdewpoint) < dewpoint_alarm:
        logger.warning('mirror temp close to dewpoint! mirror=%s, dewpoint=%s' %(Tmirror,Tdewpoint))
        #TODO: send message
        if email_acct:
            send_email()
        #TODO: turn on heater
