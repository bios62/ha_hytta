#!/bin/bash
ENV=/home/pi/py3env
PYSCRIPT=/home/pi/python-scripts/getds1820V2.py
source $ENV/bin/activate
python /home/pi/python-scripts/getds1820V2.py --tempfile - | grep '"temp"'

