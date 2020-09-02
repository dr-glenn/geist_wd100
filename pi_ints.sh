#!/bin/bash

# run pi_ints.py at system startup. must run continuously.
# python 2.7 is OK

cd /home/pi/Projects/geist_wd100
#echo "START" >> pi_ints.log
#python --version >> pi_ints.log 2>&1
python pi_ints.py >> pi_ints.log 2>&1  &
#echo "END sh" >> pi_ints.log
