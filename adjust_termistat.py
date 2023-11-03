import os
import time
import requests 
import urllib3
import sqlite3
import json
import platform
import urllib.parse
from commonV1 import *
from rpiglobals import rpiInitVariables
import argparse
import pytz
from datetime import datetime

#
#  Globals
#

defaultDebugFlag=255
debugFlagCommon=0
progVersion="getprices 14122022"

def findHourPrice(dayPrices,hour):
	count=len(dayPrices)
	for i in range (0,count):
		sTime=dayPrices[i]['time_start']
		eTime=dayPrices[i]['time_end']
		startTime=datetime.strptime(sTime[:22]+sTime[23:], '%Y-%m-%dT%H:%M:%S%z')
		if hour == startTime.hour:
			break
	if(i < count):
		return(dayPrices[i]['NOK_per_kWh'])

def getAvgPrice(dayPrices):
	if(dayPrices != False):
		#
		# Iterate over prices anc calculate todays avg price.
		#
		priceAcc=0
		count=len(dayPrices)
		for i in range (0,count):
			priceAcc=priceAcc+dayPrices[i]['NOK_per_kWh']
		avgPrice=priceAcc/count
		return(avgPrice)
	else:
		return(False)


def main():
	global debugFlagCommon
	global rpig

	print()
	print("elprice downloader version: "+progVersion)
	#
	# Get site config
	#
	if platform.system().lower() == 'linux':
		siteConfigFile="/home/pi/conf/siteconfig.json"
	else:
		siteConfigFile="g:\\demo_projects\\pi\\hytta\\config.json"

	argsParser=argparse.ArgumentParser(description='Get EL Prices')
	argsParser.add_argument("--configfile",default=siteConfigFile,type=str,help="Site Config File")
	argsParser.add_argument("--debug",default=None,type=int,help="debug flag")
	args=argsParser.parse_args()
	siteConfigFile=args.configfile
	if args.debug is None:
		debugFlagCommon=defaultDebugFlag
	else:
		debugFlagCommon=args.debug
	#
	#  Load config file
	#
	configFileName=args.configfile
	if os.path.isfile(configFileName):
		siteConfig=rpiInitVariables(siteConfigFile)
	else:
		print("Config file does not exists")
		print("Exiting")
		return(1)
	#
	try:
		with open(siteConfig.elPriceFile, "r") as infile:
			currPrice=json.load( infile)
	except:
		print("I/O Error when reading: "+siteConfig.elPriceFile)
		return(1)
	tz=pytz.timezone('Europe/Oslo')
	currentDateTime = datetime.now(tz)
	hourPrice=findHourPrice(currPrice,currentDateTime.hour)
	avgPrice=getAvgPrice(currPrice)
	print("CurrentPrice: "+str(hourPrice)+" Average Price: "+str(avgPrice))


if __name__ == '__main__':
	main()
