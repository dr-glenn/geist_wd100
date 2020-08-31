#!/bin/bash

# run pi_ints.py at system startup. must run continuously.
# python 2.7 is OK

cd /home/pi/Projects/geist_wd100
python pi_ints.py &
