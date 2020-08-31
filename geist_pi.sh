#!/bin/bash
# run environmental monitors as cron job, every 5 minutes
# (run'sudo crontab -e' to modify cron interval)
# Python 3 required, so use environment
source /home/pi/mirror-py3/bin/activate
cd /home/pi/Projects/geist_wd100
python3 geist_pi.py
python3 pi_sensors.py
