#!/bin/bash
set python-scripts scripts
for DDIR in $*
do
  DIR=/home/pi/$DDIR
  SRC=/home/pi/ha_hytta/$DDIR
  if [ -d $DIR ]; then echo $DIR exists; else mkdir $DIR;echo $DIR created; fi
  rm -rf $DIR/*
  cp $SRC/* $DIR/.
done

