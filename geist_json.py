# Use Geist JSON API

import urllib.request
import json
import pprint
import dpath.util    # conda install --channel conda-forge dpath

theURL = 'http://198.189.159.214:89'

# I see THD associated with name='Geist WD100; and with name='GTHD'

query = '/api/dev?cmd=get'
user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36'
#req = urllib.request.Request(theURL+query, headers={'User-Agent':user_agent})
req = urllib.request.Request(theURL+query)
opener = urllib.request.urlopen(req)
html = opener.read()
jdata = json.loads(html)
# Next line will show you entire JSON tree of data from Geist
#pprint.pprint(json.loads(html))

# search for key 'entity' that contains name='GTHD'. Read THD
measure_src = ['Geist WD100','GTHD']
path = 'data/*/entity/0'
#pprint.pprint(dpath.util.values(jdata,path))
for thing in dpath.util.values(jdata,path):
    if 'name' in thing:
        print('name=%s' %(thing['name']))
        if thing['name'] in measure_src:    # only want name to match "Geist WD100' or 'GTHD'
            measures = thing['measurement']
            for key in measures:
                measure = measures[key]
                # would like to print measure['units'], but not all measurements have a unit
                print('key=%s, type=%s, value=%s' %(key,measure['type'],measure['value']))
