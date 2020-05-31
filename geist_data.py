#!/usr/bin/env python
# Read environmental data from Geist Watchdog 100
# Geist provides a HTTP API that returns data as JSON.
# This program extracts temperature, humidity and dew point temperature from JSON.
# It generates either printed output to the console or HTML to be displayed in a web browser.

# Apache in Centos 7 uses Python 2.7.
# Python 2.7 does not have urllib.request
import urllib.request      # Python 3.4+
#import urllib
import json

import logging
from logging.handlers import RotatingFileHandler
# create up to 3 backup log files
handler = RotatingFileHandler('geist.log', maxBytes=50000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
handler.setFormatter(formatter)
defLogger = logging.getLogger('')
defLogger.addHandler(handler)
defLogger.setLevel(logging.INFO)
logger = logging.getLogger('__name__')

# Sample of JSON returned by /api/dev
gdata = {'data': {'2E000000E7035012': {'alarm': {'severity': '', 'state': 'none'},
                               'entity': {'0': {'alarm': {'severity': '',
                                                          'state': 'none'},
                                                'measurement': {'0': {'alarm': {'severity': '',
                                                                                'state': 'none'},
                                                                      'datalogEnabled': True,
                                                                      'displayEnabled': False,
                                                                      'state': 'normal',
                                                                      'type': 'temperature',
                                                                      'units': 'F',
                                                                      'value': '70.72'},
                                                                '1': {'alarm': {'severity': '',
                                                                                'state': 'none'},
                                                                      'datalogEnabled': True,
                                                                      'displayEnabled': False,
                                                                      'state': 'normal',
                                                                      'type': 'humidity',
                                                                      'value': '49'},
                                                                '2': {'alarm': {'severity': 'alarm',
                                                                                'state': 'tripped'},
                                                                      'datalogEnabled': True,
                                                                      'displayEnabled': False,
                                                                      'state': 'normal',
                                                                      'type': 'dewpoint',
                                                                      'units': 'F',
                                                                      'value': '50.64'}},
                                                'name': 'GTHD'}},
                               'label': 'GTHD',
                               'layout': {'0': ['entity/0']},
                               'name': 'GTHD',
                               'order': 1,
                               'snmpInstance': 1,
                               'state': 'normal',
                               'type': 'thd'},
          '740491621DC31CC3': {'alarm': {'severity': '', 'state': 'none'},
                               'analog': {'0': {'alarm': {'severity': '',
                                                          'state': 'none'},
                                                'datalogEnabled': True,
                                                'displayEnabled': False,
                                                'highLabel': '',
                                                'label': 'Analog 1',
                                                'lowLabel': '',
                                                'max': 99.0,
                                                'min': 0.0,
                                                'mode': 'customVoltage',
                                                'name': 'Analog 1',
                                                'state': 'normal',
                                                'type': '5V',
                                                'units': '',
                                                'value': '98.32'},
                                          '1': {'alarm': {'severity': '',
                                                          'state': 'none'},
                                                'datalogEnabled': True,
                                                'displayEnabled': False,
                                                'highLabel': '',
                                                'label': 'Analog 2',
                                                'lowLabel': '',
                                                'max': 99.0,
                                                'min': 0.0,
                                                'mode': 'customVoltage',
                                                'name': 'Analog 2',
                                                'state': 'normal',
                                                'type': '5V',
                                                'units': '',
                                                'value': '98.61'},
                                          '2': {'alarm': {'severity': '',
                                                          'state': 'none'},
                                                'datalogEnabled': True,
                                                'displayEnabled': False,
                                                'highLabel': '',
                                                'label': 'Analog 3',
                                                'lowLabel': '',
                                                'max': 99.0,
                                                'min': 0.0,
                                                'mode': 'customVoltage',
                                                'name': 'Analog 3',
                                                'state': 'normal',
                                                'type': '5V',
                                                'units': '',
                                                'value': '98.51'},
                                          '3': {'alarm': {'severity': '',
                                                          'state': 'none'},
                                                'datalogEnabled': True,
                                                'displayEnabled': False,
                                                'highLabel': '',
                                                'label': 'Analog 4',
                                                'lowLabel': '',
                                                'max': 99.0,
                                                'min': 0.0,
                                                'mode': 'customVoltage',
                                                'name': 'Analog 4',
                                                'state': 'normal',
                                                'type': '5V',
                                                'units': '',
                                                'value': '98.51'}},
                               'entity': {'0': {'alarm': {'severity': '',
                                                          'state': 'none'},
                                                'measurement': {'0': {'alarm': {'severity': '',
                                                                                'state': 'none'},
                                                                      'datalogEnabled': True,
                                                                      'displayEnabled': False,
                                                                      'state': 'normal',
                                                                      'type': 'temperature',
                                                                      'units': 'F',
                                                                      'value': '68.02'},
                                                                '1': {'alarm': {'severity': '',
                                                                                'state': 'none'},
                                                                      'datalogEnabled': True,
                                                                      'displayEnabled': False,
                                                                      'state': 'normal',
                                                                      'type': 'humidity',
                                                                      'value': '52'},
                                                                '2': {'alarm': {'severity': 'alarm',
                                                                                'state': 'tripped'},
                                                                      'datalogEnabled': True,
                                                                      'displayEnabled': False,
                                                                      'state': 'normal',
                                                                      'type': 'dewpoint',
                                                                      'units': 'F',
                                                                      'value': '49.83'}},
                                                'name': 'Geist WD100'}},
                               'label': 'Geist WD100',
                               'layout': {'0': ['entity/0'],
                                          '1': ['analog/0',
                                                'analog/1',
                                                'analog/2',
                                                'analog/3'],
                                          '2': ['relay/0']},
                               'name': 'Geist WD100',
                               'order': 0,
                               'relay': {'0': {'label': 'Relay 1',
                                               'mode': 'alarm',
                                               'name': 'Relay 1',
                                               'offLabel': 'De-energized',
                                               'onLabel': 'Energized',
                                               'state': 'on'}},
                               'snmpInstance': 1,
                               'state': 'normal',
                               'temperatureOffset': -5.0,
                               'type': 'BB-REL-THA4'}},
 'retCode': 0,
 'retMsg': ''}

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
    html = opener.read()
    logger.info('json size = %d' %(len(html)))
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


if __name__ == '__main__':
    logger.info('Geist fetch start')
    #gpath = ('data', '740491621DC31CC3', 'entity', '0')
    #gpath = ('data', '*', 'entity', '0', 'measurement')
    # traverse JSON nested dicts: "data/*/entity/0"
    gpath = ('data', '*', 'entity', '0')
    # Look for dict nodes tha match these data sources:
    measure_src = ['Geist WD100', 'GTHD']
    theURL = 'http://198.189.159.214:89'

    # query to get the local time
    query = '/api/sys/state?cmd=get'
    geist_state = get_geist_data(theURL, query)
    logger.debug('geist_state = %s' %(str(geist_state)))
    logger.debug('Datetime: %s' %(geist_state['data']['localTime']))

    # query to get all the data
    query = '/api/dev?cmd=get'
    geist_json = get_geist_data(theURL, query)
    # Find matching nodes: use gdata for local test, geist_json for live data
    nodes = get_path_entity(geist_json, gpath)
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

    html_out(geist_state,geist_json)
