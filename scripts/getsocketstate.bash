#!/bin/bash
#python2 tplink.py -t 192.168.0.134 -c info | grep -v 'Sent' | sed 's/'"'"'/"/g' | sed 's/u"/"/g' | jq '.'
CONFIGFILE=/home/pi/conf/siteconfig.json
SOCKETLISTDIR=`cat $CONFIGFILE | jq '.logDirectory' | sed 's/"//g'`
SOCKETS=` cat $SOCKETLISTDIR/tpsockets | cut -d ' ' -f 1` 
source /home/pi/tplink_venv_py27/bin/activate
for I in $SOCKETS
do
RESULT=`python2 /home/pi/python-scripts/tplink.py -t $I -c info`
if [ $? -eq 0 ]
then
  # a socket for the given IP address is found
  # Evaluate socket relay state and echo it
  #
  STATUS=`echo $RESULT |  awk -F')' '{$1="";result=$0;sub(/ system$/,"",result);gsub("\047","\"",result);gsub("u\"","\"",result); print result}'`
 echo $STATUS | jq '.system.get_sysinfo | "\(.alias) \(.relay_state)"' | awk '{gsub("\"","");if ($2 == "0") {printf("%s OFF\n"),$1} else {printf("%s ON\n"),$1}}'
# echo $STATUS| jq '.system.get_sysinfo | "\(.alias) \(.relay_state)"' 
else
 # No scokect is found on the IP adress
 #
 SOCKET=`cat $SOCKETLISTDIR/tpsockets | grep $I `
  echo "$SOCKET not available"
fi
done


