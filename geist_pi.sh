#!/bin/bash
source /home/pi/mirror-py3/bin/activate
cd /home/pi/Projects/geist_wd100
python3 geist_pi.py
#tail -1 geist_data.log > geist_newest.dat
python3 pi_sensors.py
#tail -1 pi_data.log > pi_newest.dat
