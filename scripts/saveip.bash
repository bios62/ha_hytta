#!/bin/bash
uday=`date '+%u'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
#SCRIPT=`echo $0 | cut -f 1 -d '.'`
SCRIPT=`basename $0 |cut -f 1 -d '.'` 
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
date >> $LOGFILE
curl -i -k -H 'Content-Type: application/json' https://revebaasen.no/php/saveipV3.php?siteid=hytta  2>/dev/null| grep '89.' >>$LOGFILE

