#!/usr/bin/env python
# Read environmental data from Geist Watchdog 100
# Geist provides a HTTP API that returns data as JSON.
# This program extracts temperature, humidity and dew point temperature from JSON.
# It generates either printed output to the console or HTML to be displayed in a web browser.

# Apache in Centos 7 uses Python 2.7.
# Python 2.7 does not have urllib.request
import urllib.urequest      # Python 3.4+
import json

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
            for n in node:
                nnode = get_path_entity(node[n],path[index+1:])
                nnodes.extend(nnode)
            break
        elif isinstance(p,(tuple,list)):
            nnodes = []
            for n in node:
                if n in p:
                    nnode = get_path_entity(node[n],path[index+1:])
                    nnodes.extend(nnode)
        else:
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
    opener = urllib.urequest.urlopen(theURL + query)
    html = opener.read()
    jdata = json.loads(html)
    return jdata

def get_measures(geist_data):
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
    return instrument
    
def html_out(dt, instrument):
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
    out = out0 %(dt)
    for instr in instrument:
        instr_str = '<H3>%s</H3>' %(instr)
        measures = instrument[instr]
        for key in measures:
            instr_str += '<p>%s: %s %s</p>' %(key,measures[key][0],measures[key][1])
        out += instr_str
    out += out1
    print(out)  # sends HTML to HTTP stream

def oled_out(dt,instrument):
    oled.fill(0)
    oled.text(dt, 0, 0)
    i = 0
    for instr in instrument:
        j = 1
        if i == 0:  # oled only has room for 1
            oled.text(instr, 0, j*10)
            j += 1
            measures = instrument[instr]
            for key in measures:
                oled.text(measures[key][0][:5]+": "+measures[key][1], 0, j*10)
                j += 1
        i += 1
    oled.show()

def main():
    # query to get the local time
    query = '/api/sys/state?cmd=get'
    geist_state = get_geist_data(theURL, query)
    dt = geist_state['data']['localTime']
    print('Datetime: {}'.format(dt))
    geist_state = None
    # query to get all the data
    query = '/api/dev?cmd=get'
    geist_json = get_geist_data(theURL, query)
    instruments = get_measures(geist_json)
    #html_out(dt, instruments)
    oled_out(dt, instruments)
    
if __name__ == '__main__':
    from machine import I2C,Pin
    import ssd1306
    print('Geist fetch start')
    i2c = I2C(-1,scl=Pin(4),sda=Pin(5))
    oled = ssd1306.SSD1306_I2C(128,64,i2c)
    #gpath = ('data', '740491621DC31CC3', 'entity', '0')
    #gpath = ('data', '*', 'entity', '0', 'measurement')
    # traverse JSON nested dicts: "data/*/entity/0"
    gpath = ('data', '*', 'entity', '0')
    # Look for dict nodes tha match these data sources:
    measure_src = ['Geist WD100', 'GTHD']
    theURL = 'http://198.189.159.214:89'
    t = 0
    dminute=5
    nhours=6
    while t < nhours*60/5:
        main()
        t += 1
        utime.sleep(dminute*60)
    