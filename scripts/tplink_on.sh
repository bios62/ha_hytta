#!/bin/bash
source $HOME/tplink_env/bin/activate
PYSCRIPT=tplink.py
cd $HOME/python-scripts
export IP=`cat $HOME/scripts/IPADDR`
python $PYSCRIPT -t $IP -j '{"system":{"set_relay_state":{"state":1}}}'
python $PYSCRIPT -t $IP -c info
