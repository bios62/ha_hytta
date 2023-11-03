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
FILE=`cat /home/pi/conf/siteconfig.json | jq '.remotetempfile' | sed 's/"//g'`
PYSCRIPT=getds1820.py
date >> $LOGFILE
#
# setup environment
#
REMTEMP=`sshpass -f /home/pi/conf/remotepwd ssh pi@stue-pi "python /home/pi/python-scripts/$PYSCRIP --tempfile - 2>/dev/null"`
if [ $? -ne 0 ]
then
  rm $FILE
  exit $?
fi
#JSONTEMP=`echo '{"temp":"'${REMTEMP}'"}'`
#echo $JSONTEMP>>$FILE
#echo "Captured "${JSONTEMP} >>$LOGFILE
echo ${REMTEMP} >>$LOGFILE
echo $REMTEMP>$FILE

