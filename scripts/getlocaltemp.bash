#!/bin/bash
#
#  getlocaltemp
#  Changelog
#  22/8-2022 Initial Code
#
#  fetches local ds1820 temp
#
# Do sudo to root to execute python script
#
SCRIPT=`basename $0 |cut -f 1 -d '.'`
uday=`date '+%u'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
date >> $LOGFILE
LOCALTEMPFILE=`cat /home/pi/conf/siteconfig.json | jq '.localtempfile' | sed 's/"//g'`
#sudo bash -c "source /home/pi/tplink_env/bin/activate;python3 /home/pi/python-scripts/getds1820.py --tempfile $LOCALTEMPFILE.tmp" >>$LOGFILE
sudo bash -c "source /home/pi/py39/bin/activate;python3 /home/pi/python-scripts/getds1820.py --tempfile $LOCALTEMPFILE.tmp" >>$LOGFILE
sudo cp $LOCALTEMPFILE.tmp $LOCALTEMPFILE
sudo chown pi:pi $LOCALTEMPFILE
