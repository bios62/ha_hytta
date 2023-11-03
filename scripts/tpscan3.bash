#!/bin/bash
#
# Updated: 14/8-2023
#
# Scans all devices and updates IP adresses of connected TPLINK devices
# 14/8-23: Changed to python3 and tplib3
#
uday=`date '+%u'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
RESULTFILE=${LOGDIR}/tpsockets.tmp
SOCKETCONFIGFILE=`cat /home/pi/conf/siteconfig.json | jq '.socketConfigFile' | sed 's/"//g'`
source $HOME/py39/bin/activate
cd $HOME/python-scripts
DATO=`date`
echo "# Updated: " $DATO >>$LOGFILE
python3 /home/pi/python-scripts/tpscan3.py --subnet 192.168.0.1 --ipstart 130 --ipend 145 --tpport 9999 --resultfile $RESULTFILE >>$LOGFILE
# 
# Need some sanity check
#
mv $RESULTFILE $SOCKETCONFIGFILE
