# These are settings for Geist logger on Raspberry Pi
import os
if os.path.isfile('pi_settings.py'):
    import pi_settings as gset
    dewpoint_alarm = gset.dewpoint_alarm
    dewpoint_temp = gset.dewpoint_temp
    mirror_temp = gset.mirror_temp
    geist_addr = gset.geist_addr
    geist_port = gset.geist_port
else:
    dewpoint_alarm = 4.0    # diff between ambient dewpoint and mirror temperature in F
    dewpoint_temp = ('Geist WD100','dewpoint')
    mirror_temp = ('GTHD','temperature')

    geist_addr = 'http://198.189.159.214'   # address of geist Watchdog
    geist_port = 89     # use None for default port value

