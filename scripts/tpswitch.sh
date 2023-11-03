#!/bin/bash
# Pretty obsolete....
# missing source of correct pyenv, missing usage of siteconfig
#
RESULTFILE=${LOGDIR}/tpsockets.tmp
SOCKETCONFIGFILE=`cat /home/pi/conf/siteconfig.json | jq '.socketConfigFile' | sed 's/"//g'`
source $HOME/py39/bin/activate
export PYSCRIPT_HOME=$HOME/python-scripts
if [  ! -f $SOCKETCONFIGFILE ] || [ "$1" = "" ]
then
  echo "usage: tpswitch place on|off|status"
  exit 1
fi
SOCKET=`grep $1 $SOCKETCONFIGFILE`
if [ ! "$SOCKET" = "" ]
then
  export IP=`echo $SOCKET  | cut -d ' ' -f 2 `
  if [ "$2" = "on" ]
  then
    RELAY='{"system":{"set_relay_state":{"state":1}}}'
  elif [ "$2" = "off" ]
  then 
    RELAY='{"system":{"set_relay_state":{"state":0}}}'
  elif [ "$2" = "status" ]
  then 
    RELAY=''
  else
   echo "Ulovlig funksjon, gyldig verdi er on|off|status"
   exit 1
  fi
  if [ "$RELAY" != "" ]
  then
    python $PYSCRIPT_HOME/tplink3.py -t $IP -j $RELAY
  fi
  python $PYSCRIPT_HOME/tplink3.py -t $IP -c info 
else
  echo "ukjent plassering"
  exit 1
fi
exit 0
