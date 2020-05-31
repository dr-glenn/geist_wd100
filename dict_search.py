# Search nested dicts with wildcard specification
# here is a simple discussion of the problem: https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys?noredirect=1&lq=1

d_test = {'root': {
                '1a':{
                  '2a':{
                      '3a':'measure_a'
                  }
                },
                '1b':{
                  '2a':{
                      '3b':'measure_b'
                  }
                }
              }
            }

path = ('root','1a','2a')
path = ('root','*','2a')

def get_path_entity(dataDict,path):
    nodes = []
    nnodes = None
    node = dataDict
    for index,p in enumerate(path):
        if p == '*':
            # recurse over all nodes in current node
            nnodes = []
            print('p = *, handle %s' %(str(path[index+1:])))
            print('node = %s' %(str(node)))
            for n in node:
                print('n = %s' %(str(n)))
                nnode = get_path_entity(node[n],path[index+1:])
                print('nnode = %s' % (str(nnode)))
                nnodes.extend(nnode)
            break
        elif isinstance(p,(tuple,list)):
            pass    # eek, what to do?
            # call get_path_entity again with current node and remainder of path items.
            # it will return with a list of nodes that should be appended to current nodes.
        else:
            print('index = %d, p = %s, node = %s' %(index,p,str(node)))
            print('p = %s, node[p] = %s' %(p,str(node[p])))
            node = node[p]
    if nnodes:
        nodes.extend(nnodes)
    else:
        nodes.append(node)
    return nodes

node = get_path_entity(d_test,path)
print('get_path_entity')
print(node)

from collections import abc
def nested_dict_iter(nested):
    for key, value in nested.items():
        if isinstance(value, abc.Mapping):
            yield from nested_dict_iter(value)
        else:
            yield key, value

print('nest_dict_iter:')
print(list(nested_dict_iter(d_test)))

def gen_dict_extract(key, var):
    if hasattr(var,'iteritems'):
        for k, v in var.iteritems():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result
print('gen_dict_extract')
print(gen_dict_extract('3a',d_test))

import geist_data as mydata
gpath = ('data','740491621DC31CC3','entity','0')
gpath = ('data','*','entity','0','measurement')
gpath = ('data','*','entity','0')
measure_src = ['Geist WD100','GTHD']

nodes = get_path_entity(mydata.gdata, gpath)
print('get_path_entity')
print(nodes)
for node in nodes:
    if 'name' in node and node['name'] in measure_src:
        meas_nodes = get_path_entity(node,('measurement',))
        print ('name=%s\n  measures=%s' %(node['name'],str(meas_nodes)))
        for items in meas_nodes:
            for key in items:
                print('key=%s' %(key))
                print('type=%s, value=%s' %(items[key]['type'], items[key]['value']))
