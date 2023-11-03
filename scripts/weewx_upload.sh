#!/bin/sh
#
# Set up log
#
uday=`date '+%u'`
LOGFILE=/home/pi/logs/weewx_${uday}.log
TMPFILE=/home/pi/logs/curltmp
PASSWD='mercedes450sl'
date >>$LOGFILE
#
# Set up wget and propagate filename
#
weetime=`date +'%m%d%H'`
wgetURL='https://revebaasen.no/php/savepropertyV2.php?siteid=weewx&propertyname=weatherid&propertyvalue='${weetime}
#echo $wgetURL | wget -i - -a $LOGFILE -O /home/pi/logs/wget.out
curl -i $wgetURL >$TMPFILE 2>/dev/null
grep 'HTTP/1.1 200 OK' $TMPFILE >/dev/null
if [ $? -ne 0 ] 
then
  cat $TMPFILE >>$LOGFILE
else
  echo "curl HTTP/1.1 200 OK" >>$LOGFILE
fi
#
# Build archove for transfer
#
cd /var/www/html
tar -czvf weewx.tar.gz weewx
#
# Transfer and set directory acordingly
#
sshpass -p $PASSWD scp /var/www/html/weewx.tar.gz revebaasen.no@ssh.revebaasen.no:/www/vaer/weewx.tar.gz
sshpass -p $PASSWD ssh revebaasen.no@ssh.revebaasen.no "cd /www/vaer/;rm weewx.tar;mv weewx${weetime} weewx_old;rm -rf weewx_old;gunzip weewx.tar.gz;tar -xvf weewx.tar;mv weewx weewx"${weetime}


