import os
import glob
import time
import json
import platform
import argparse
from datetime import datetime

#
# Run as root
#
# python 3
#
# Change log: 
#  22/8-22 refreshed, updated to use rpiglobals.py
#  5/10-22, rpiglobals, removed, onl one parameter was needed, add as commandline parameter instead
#  if localtempfile = '-' only printing to stdout
#
# Usage:
# python getds1820Vx.py [--tempfile filename_to_store_result | tempfile -]

progVersion="getds1820 1.0 22082022"


#
# Load w1-gpio and w1-therm
#
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

tempstat={}

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def write_temp_local(filename,tempstat):
	f=open(filename,'w')
	f.write(tempstat)
	f.close()

#
#  Small helper function open and read all lines in ds1820 
#  sensor file in filesystem
def readTempRaw(rawtempfile):
	try:
		f = open(rawtempfile, 'r')
		lines = f.readlines()
		f.close()
		return lines
	except Exception as e:
		print(e)
		return(False)

def read_temp(filename):
	lines = readTempRaw(filename)
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_c
		
		
def main():
	#
	# get the file to store the result
	#
	if platform.system().lower() == 'linux':
		localTempFile="/u01/iot/localtempfile"
	else:
		localTempFile="g:\\demo_projects\\pi\\hytta\\config.json"
	argsParser=argparse.ArgumentParser(description='ds1850 temperatur fetching program')
	argsParser.add_argument("--tempfile",default=localTempFile,type=str,help="File to store result")
	args=argsParser.parse_args()
	localTempFile=args.tempfile
	# get the current time
	now=datetime.now() # current date and time
	date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
	tempstat['temp']=read_temp(device_file)
	tempstat['time']=date_time
	if not (localTempFile == '-'):
		write_temp_local(localTempFile,json.dumps(tempstat))
	print(json.dumps(tempstat))
if __name__ == '__main__':
	main()