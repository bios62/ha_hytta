import requests 
import json
import urllib.parse
import os.path
import sqlite3
from tplib3 import *
import datetime
from sqlite3 import Error

progVersion="280320120"
siteConfigFile="C:\\usr\\demo_projects\\pi\\hytta\\config.json"



def getGroups(siteConfig):
	#
	#  Fetch all groups
	#
	headers = {"content-type": "application/json"}
	g = requests.get(siteConfig['groupConfigURL'], headers=headers)
	localConfig=[]
	if g.ok :
		#
		# Fetch memerships
		#
		m=requests.get(siteConfig['membersURL'], headers=headers)
		if(m.ok):
			allGroups=g.json()['items']
			allmembers=m.json()['items']
			#
			# Iterate through and add member array
			#
			for group in list(allGroups):
				#
				# iterate through all memers of a group
				#
				members=[]
				for member in list(allmembers):
					if(member['groupname'] == group['groupname']):
						members.append(member['membername'])
				group['members']=members
				localConfig.append(group)
			f=open(siteConfig['groupConfigFile'],"w")
			f.write(json.dumps(localConfig))
			f.close()
			return(localConfig)
		else:
			print("API call for members failed: "+str(m.status_code))
			return(False)
	else:
		print("API call for groups failed: "+str(g.status_code))
		return(False)

def getDesiredTempSetting(tempSettingURL):
    headers = {"content-type": "application/json"}
    r = requests.get(tempSettingURL, headers=headers)
    if r.ok :
        return(r.json()['items'])
    else:
        return(False)
#
# Loads site local configuration
#
# loads group memer configuration from file, assumes changes are rare
# if the file is not found, loads from iot service
#
def loadSiteConfig(siteConfigFile):
	#
	# Load master config file to get groupConfigFile path,
	# confURL, for static group membership
	# tempConfigURL for dynamic temp setting
	# groupconfig, contains statig gruop names and group sensor setup
	#
	allConfig={}
	try:
		f=open(siteConfigFile,"r")
		strsiteconfig=f.read()
		siteConfig=json.loads(strsiteconfig)
	except IOError:
		print("Site Config File"+siteConfigFile+" is not accessible")
		return(False)
	finally:
		f.close()

	tempSettingURL=siteConfig['tempSettingURL']
	groupConfigFileName=siteConfig['groupConfigFile']
	socketConfigFileName=siteConfig['socketConfigFile']
	#
	# Load static membership, 
	# if file exists, load local file
	# if not fetch form OT database
	#
	if os.path.isfile(groupConfigFileName):
		try:
			f=open(groupConfigFileName,"r")
			strconfig=f.read()
			groups=json.loads(strconfig)
		except IOError:
			print("Member Config File"+groupConfigFileName+" exists bt is not accessible")
			return(False)
		finally:
			f.close()
	else:
	# 
	# Group Config did not exists need to fetch it from iot database
	#
		groups=getGroups(siteConfig)
	#
	# Read the socket input file and add it to a dict
	# File is in host format  ip name
	# stored as an array  the config json
	allSockets=[]
	try:
		fp=open(socketConfigFileName)
		line=fp.readline().strip('\n')
		allSockets=[]
		while (line):
			pos=line.find(' ')
			ip=line[:pos]
			host=line[pos+1:].lstrip()
			sockets={}
			sockets['socketname']=host
			sockets['ip']=ip
			allSockets.append(sockets)
			line=fp.readline().strip('\n')
	except IOError:
		print("Socket Config File "+socketConfigFileName+" exists but is not accessible")
		return(False)
	#
	# build dics result
	#
	
	allConfig['groups']=groups
	allConfig['siteConfig']=siteConfig
	allConfig['tpSockets']=allSockets
	return(allConfig)

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
#
# Fetches the temp for a given group, from the sensors, based on groupname, and metdot/file
# ds1820 type devices read temp from line 2 of a specific file, temp is coded without .
#
# weewx reads from sqlite db
#
#  Caller is responsible for veriyfing that group is active
#
#  Return fetched temp
#  If temp reading for som reason is not possible, return False
#
def getTempForGroup(group):
    #
	# Verify if inuse is set to Y
	#
	if(group['inuse'] != 'Y'):
		print("getTempForGorup error: Group: "+group['groupname']+" has not set inuse flag")
		return(False)
	#
	#  Split on sensor type
	#  ds1820 reads from a file
	#
	if group['sensortype'] == 'ds1820':
		# ds1820 type, read from file
		temp_c=False
		lines=readTempRaw(group['sensorconfig'])
		loopCount=0            # Block for hanging for ever
		maxLoops=20
		while   (loopCount<maxLoops):  # Need to loop in case we ar just in a sensor read cycle
			if(not lines):        # Max loops
				time.sleep(0.2)
				lines = readTempRaw()
				loopCount+=1
			elif lines[0].strip()[-3:] != 'YES': # File not ready
				time.sleep(0.2)
				lines = readTempRaw()
				loopCount+=1
			else:
				break
			#
			# If loop ends with cloopCount=20 we did not succseed in readin the file
			#
		if(loopCount <maxLoops):
			equal_pos = lines[1].find('t=')
			if equal_pos != -1:
				temp_string = lines[1][equal_pos+2:]
				temp_c = float(temp_string) / 1000.0
				return(temp_c)
			else:
				print("getTempForGorup error: Group: "+group['groupname']+" wrong format in file")
				print(lines)
				temp_c=False
		else:
			print("getTempForGorup error: Group: "+group['groupname']+" File Read Error")
			return(False)
	elif group['sensortype'] == 'weewx':
		#
		# read from sqlite
		#
		conn = None
		#
		#  Set up a sqllite connection to a target
		#
		try:
			conn = sqlite3.connect(group['sensorconfig'])
		except Error as e:
			print(e)
			print("getTempForGorup error: Group: "+group['groupname']+" could not open sqllite db")
			return(False)  # Exit if connection fails
		#
		# Read the temp from the weewk db
		#		
		outdoorTemp=False
		cur = conn.cursor()
		sqlstmt="select inTemp,ifnull(outTemp,-22),datetime from archive  where datetime="
		sqlstmt=sqlstmt+"(select max(datetime) from archive)"
		cur.execute(sqlstmt)
		rows = cur.fetchall()
		inTemp=((rows[0])[0]-32)/1.8
		return(inTemp)
	else:
		print("getTempForGorup error: Group: "+group['groupname']+" not imlemented")
		return(False)
	return(False)
def printResult(result):
	if( u'set_relay_state' in result["system"]):
		print(" Command, Error Code: "+str(result["system"]["set_relay_state"]["err_code"]),end=' ')
	elif (u'get_sysinfo' in result["system"]):
		print(" Relay state: "+str(result["system"]["get_sysinfo"]["relay_state"]))
	else:
		print(" Unknown result ")
		print(result)
#
# toggleRelay
# Last changed 3173-2020
#
# turns a tplink socket on or off
# Parameters
#	socketList		list of all sockets
#	relayList		list of all sockets to be canged
#	state			ON or OFF
#
# the funtion return False upon either socket not found or scket creatin failed
#
def toggleRelay(socketList,relayList,state):
	#
	# iterate through the list of sockets and verify if it esist in the list of sockets to be changed
	#
	# 
	#  Iterate through the list of relays and find matchin socket
	#
	for relay in list(relayList):
		#
		# Iterate over sockets to get IP address
		#
		onsw='{"system":{"set_relay_state":{"state":1}}}'
		offsw= '{"system":{"set_relay_state":{"state":0}}}'
		info='{"system":{"get_sysinfo":{}}}'
		relayCommand=onsw
		if state == 0:
			relayCommand=offsw
		elif state == 1:
			relayCommand=onsw
		else:
			relayCommand=info
		socketFound=False
		for i in range(len(socketList)):
			if relay == socketList[i]['socketname']:
				print(socketList[i]['socketname']+" "+socketList[i]['ip'])
				result=do_tplink(socketList[i]['ip'],relayCommand,9999)
				if (result):
					printResult(result)
				else:
					print("Connection failure "+socketList[i]['ip'])
				socketFound=True
		if(not socketFound):
			print("Socket:"+relay+" Not found in socket hostfile")
			return(False)
	return(True)

#
# turn socket on or off based 2 conditions
#   group is inuse
#   temp is outside range
# 
def termostat(allConfig,desiredTemp):

	#
	# iterate through all groups, static values
	#
	for member in list(allConfig['groups']):
		#
		# Iterate through all current settings and fetch sensor temp value and desired temp
	 	#
		if member['inuse'] == 'Y':
			currentTemp=getTempForGroup(member)
			#
			# If current temp is 0.5 below desiredTemp, flip on sockets
			# If current temp is 0,5 above desiredtemp, flip off sockets
			# desiredtemp s based on which of the two settings applies
			#
			# Iterate through desiredTemp dict and find high/low/ and selected
			for tempSetting in list(desiredTemp):
				if tempSetting['groupname'] == member['groupname']:
					if tempSetting['selectedtemp'] == "L":
						dtemp=tempSetting['lowtemp']
					else:
						dtemp=tempSetting['hightemp']
			if (currentTemp-0.5)<dtemp:
				toggleRelay(allConfig['tpSockets'],member['members'],1)
			elif (currentTemp+0.5)>dtemp:
				toggleRelay(allConfig['tpSockets'],member['members'],0)


def main():

	print("getconfig version: "+progVersion+" "+datetime.datetime.now().strftime("%d/%m-%Y %H:%M:%S"))
	print()
	#
	# Load static group config information
	#
	allConfig=loadSiteConfig(siteConfigFile)
	if not allConfig:
		print("Error Loading confguration")
		return(1)
	#
	# Fetch dynamic temp settion
	#
	desiredTemp=getDesiredTempSetting(allConfig['siteConfig']['tempSettingURL'])
	#print(allConfig['groups'])
	#print(allConfig['tpSockets'])
	#print(desiredTemp)
	#
	# Process termostat
	#
	termostat(allConfig,desiredTemp)
	#
	print("Termostat setting completed")


if __name__ == '__main__':
	main()