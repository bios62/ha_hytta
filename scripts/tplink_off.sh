#!/bin/bash
PYSCRIPT=tplink.py
source $HOME/tplink_env/bin/activate
cd $HOME/python-scripts
export IP=`cat $HOME/scripts/IPADDR`
python $PYSCRIPT -t $IP -j '{"system":{"set_relay_state":{"state":0}}}'
python $PYSCRIPT -t $IP -c info
