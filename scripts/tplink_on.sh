#!/bin/bash
source $HOME/tplink_env/bin/activate
cd $HOME/python-scripts
export IP=`cat $HOME/scripts/IPADDR`
python tplink.py -t $IP -j '{"system":{"set_relay_state":{"state":1}}}'
python tplink.py -t $IP -c info
