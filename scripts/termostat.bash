#!/bin/bash
#
# Updated: 22/8-2022
#
#  Downloads static groupconfig from cloud
#
uday=`date '+%u'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
CONFIGFILE=/home/pi/conf/siteconfig.json
PYSCRIPT=termostat.py
date >> $LOGFILE
#
# setup environment
#
source $HOME/py39/bin/activate
#
# Run python script
#
cd /home/pi/python-scripts
python3 $PYSCRIPT --configfile $CONFIGFILE >>$LOGFILE
