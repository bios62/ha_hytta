import requests
import json
import sys
import urllib.parse
import os.path
from tplib import *
from common import *

# from rpiglobals import rpiInitVariables
import datetime
import pytz
from datetime import datetime
import time
import platform
import argparse
from sqlite3 import Error

# termostatV10
#
#  V4 Update: Adjuster interval +/- 0.5 of dtemp
#  V5 and V6: experimental, abandoned
#
#  V7 added funtion for dynamic settin of low temp based on time interval
#  Current version, no real funtion
#  V7 More failsafe code for reading temp sensors, migrated out to sensorlib.py
#  V9 added adjust of termostat based on price table
#  V9 switched from sensorlib.py to commonV1.py
#  V10 replaced CommonV1 with commonV2.py, commonv2 uses snake_case not CammelCase for functions
#
# Fetches config info about active zones from file
# Fecthes and saves temp settings for active zones from cloud
# fetches sockets for active zones
# Check relay state for active zones
# if temp deviates with more thatn +/- 0.5 degree, sets relays in zone accordingly
#
# Python version: 3
# E
# Modifictions
# 	5/8-20 added save of desired temp in main
#   4/8-20 Added support for platform to set default siteConfigFile
#   3/2-21  Adjusted dtemp interval. Not implemented
#   2/4-21 Changed togle relay not to return if single member in group was not found
#   25/9-22 Added adjustTemp funtion for dynamic selection when temp is low, not implemented, only using defaultTemp
#   25/9-22 Restructured code for readin of sensors, moved to sensorlib
# 	25/9 added adjust temp function, no real value
# 	25/9 added calcualtion of age of temp files for remote and local
# 	25/9 Added backuptemp calculation
#   22/10 CLeaned up termostat code
#   8/10-23 migrated to commonV2
#
# Usage:
# python termostatV9.py [--configfile filename]

progVersion = "1.0 22102022"

if platform.system().lower() == "linux":
    siteConfigFile = "/home/pi/conf/siteconfig.json"
else:
    siteConfigFile = "C:\\usr\\demo_projects\\pi\\hytta\\config.json"


def getGroupsNLA_moved_to_CommonV2(siteConfig):
    #
    #  Fetch all groups
    #
    headers = {"content-type": "application/json"}
    g = requests.get(siteConfig["groupConfigURL"], headers=headers)
    localConfig = []
    if g.ok:
        #
        # Fetch memerships
        #
        m = requests.get(siteConfig["membersURL"], headers=headers)
        if m.ok:
            allGroups = g.json()["items"]
            allmembers = m.json()["items"]
            #
            # Iterate through and add member array
            #
            for group in list(allGroups):
                #
                # iterate through all memers of a group
                #
                members = []
                for member in list(allmembers):
                    if member["groupname"] == group["groupname"]:
                        members.append(member["membername"])
                group["members"] = members
                localConfig.append(group)
            f = open(siteConfig["groupConfigFile"], "w")
            f.write(json.dumps(localConfig))
            f.close()
            return localConfig
        else:
            print("API call for members failed: " + str(m.status_code))
            return False
    else:
        print("API call for groups failed: " + str(g.status_code))
        return False


def getDesiredTempSetting(tempSettingURL):
    print("Fetching desired temp setting")
    headers = {"content-type": "application/json"}
    r = requests.get(tempSettingURL, headers=headers)
    if r.ok:
        return r.json()["items"]
    else:
        return False


#
# Loads site local configuration
#
# loads group memer configuration from file, assumes changes are rare
# if the file is not found, loads from iot service
#
def loadSiteConfig_NLU(siteConfigFile):
    #
    # Load master config file to get groupConfigFile path,
    # confURL, for static group membership
    # tempConfigURL for dynamic temp setting
    # groupconfig, contains statig gruop names and group sensor setup
    #
    allConfig = {}
    try:
        f = open(siteConfigFile, "r")
        strsiteconfig = f.read()
        siteConfig = json.loads(strsiteconfig)
        f.close()
    except IOError:
        print("Site Config File" + siteConfigFile + " is not accessible")
        return False

    tempSettingURL = siteConfig["tempSettingURL"]
    groupConfigFileName = siteConfig["groupConfigFile"]
    socketConfigFileName = siteConfig["socketConfigFile"]
    #
    # Load static membership,
    # if file exists, load local file
    # if not fetch form OT database
    #
    if os.path.isfile(groupConfigFileName):
        try:
            f = open(groupConfigFileName, "r")
            strconfig = f.read()
            groups = json.loads(strconfig)
            f.close()
        except IOError:
            print(
                "Member Config File"
                + groupConfigFileName
                + " exists but is not accessible"
            )
            return False
    else:
        #
        # Group Config did not exists need to fetch it from iot database
        #
        groups = get_groups(siteConfig)
    #
    # Read the socket input file and add it to a dict
    # File is in host format  ip name
    # stored as an array  the config json
    allSockets = []
    try:
        fp = open(socketConfigFileName)
        line = fp.readline().strip("\n")
        allSockets = []
        while line:
            pos = line.find(" ")
            ip = line[:pos]
            host = line[pos + 1 :].lstrip()
            sockets = {}
            sockets["socketname"] = host
            sockets["ip"] = ip
            allSockets.append(sockets)
            line = fp.readline().strip("\n")
    except IOError:
        print(
            "Socket Config File "
            + socketConfigFileName
            + " exists but is not accessible"
        )
        return False
    #
    # build dics result
    #

    allConfig["groups"] = groups
    allConfig["siteConfig"] = siteConfig
    allConfig["tpSockets"] = allSockets
    return allConfig


#
# printResult
#
# Prints resut of setting relay state
#
def printResult(result):
    if "set_relay_state" in result["system"]:
        print(
            " Command, Error Code: "
            + str(result["system"]["set_relay_state"]["err_code"]),
            end=" ",
        )
    elif "get_sysinfo" in result["system"]:
        print(" Relay state: " + str(result["system"]["get_sysinfo"]["relay_state"]))
    else:
        print(" Unknown result ")
        print(result)


#
# toggleRelay
# Last changed 3173-2020
#
# turns a tplink socket on or off
# Parameters
# 	socketList		list of all sockets
# 	relayList		list of all sockets to be canged
# 	state			ON or OFF
#
# the funtion return False upon either socket not found or scket creatin failed
#
def toggleRelay(socketList, relayList, state):
    #
    # iterate through the list of sockets and verify if it esist in the list of sockets to be changed
    #
    #
    #  Iterate through the list of relays and find matchin socket
    #
    print(json.dumps(relayList))
    for relay in list(relayList):
        #
        # Iterate over sockets to get IP address
        #
        onsw = '{"system":{"set_relay_state":{"state":1}}}'
        offsw = '{"system":{"set_relay_state":{"state":0}}}'
        info = '{"system":{"get_sysinfo":{}}}'
        relayCommand = onsw
        if state == 0:
            relayCommand = offsw
        elif state == 1:
            relayCommand = onsw
        else:
            relayCommand = info
        socketFound = False
        for i in range(len(socketList)):
            if relay == socketList[i]["socketname"]:
                print(
                    "  Device: "
                    + socketList[i]["socketname"]
                    + " "
                    + socketList[i]["ip"]
                    + " CMD:"
                    + relayCommand
                )
                result = do_tplink(socketList[i]["ip"], relayCommand, 9999)
                if result:
                    print("    ", end=" ")
                    printResult(result)
                    result = do_tplink(socketList[i]["ip"], info, 9999)
                    print("    ", end=" ")
                    printResult(result)
                else:
                    print("     Connection failure " + socketList[i]["ip"])
                socketFound = True
        if not socketFound:
            print("     Socket:" + relay + " Not found in socket hostfile")
            # return(False)  // Continue for rest of members f group
    return True


#
# turn socket on or off based 2 conditions
#   group is inuse
#   temp is outside range
#
def termostat(allConfig, desiredTemp):
    #
    # iterate through all groups, static values
    #
    currentTemp = {}

    for member in list(allConfig["groups"]):
        #
        # Iterate through all current settings and fetch sensor temp value and desired temp
        #
        if member["inuse"] == "Y":
            #
            # If current temp is 0.5 below desiredTemp, flip on sockets
            # If current temp is 0,5 above desiredtemp, flip off sockets
            # desiredtemp is based on which of the two settings applies
            #
            # Iterate through desiredTemp dict and find high/low/ and selected

            #
            #  Correction logic for usage of adjusted temp is added
            #  Iterate over desiretemp, to find desiretemp for group that match current group
            #  If not found dtemp== False
            #
            dtemp = False  # Generate error in code if not set
            for tempSetting in list(desiredTemp):
                if tempSetting["groupname"] == member["groupname"]:
                    currentTempSetting = tempSetting["selectedtemp"]
                    if (
                        tempSetting["selectedtemp"] == "L"
                        and member["usetermostat"] == "Y"
                    ):
                        dtemp = adjustTemp(
                            allConfig["siteConfig"],
                            tempSetting["lowtemp"],
                            tempSetting["adjustedtemp"],
                        )
                    elif (
                        tempSetting["selectedtemp"] == "H"
                        and member["usetermostat"] == "Y"
                    ):
                        dtemp = tempSetting["hightemp"]
                    break
                #
            #
            if (
                member["usetermostat"] == "Y"
            ):  # Slave config not implemented stue ekstra
                #  Find current temp for group
                #
                if dtemp is False:  # Severe error, termostat is Y but no setpoint
                    print(
                        "Temp setpoint for group: " + member["groupname"] + " Not Found"
                    )
                    return False
                #
                # Find current temp for the group
                #
                # 12/2-2023 this code is not safe, needs to be restructured as not all temp are found, including backuptemp
                #
                ctemp = get_temp_for_group(
                    allConfig["siteConfig"],
                    member,
                    int(allConfig["siteConfig"]["maxAgeInHours"]),
                )
                if ctemp is False:
                    print(
                        "Severe error: temp not found for: "
                        + member["groupname"]
                        + " "
                        + allConfig["siteConfig"][member["sensorconfig"]]
                    )
                # 	ctemp=getBackupTemp(member['groupname'],currentTemp)
                # 	if ctemp is not False:
                # 		print('Using backuptemp for '+member['groupname'])

                #
                # If no current temp is found exit
                #
                # if ctemp is False:
                # 	print("Severe error: backuptemp not found for: "+member['groupname'])
                # 	return(False)   # SHALL NOT EXIT stops processing
                #
                #  Flip relay on or off dependentent on temp deviation
                #
                if not ctemp == False:
                    if float(ctemp["temp"]) < (dtemp - 0.5):  # temp to low
                        print(
                            "Group: "
                            + member["groupname"]
                            + " temp to low: set temp: "
                            + str(dtemp).strip("\n")
                            + " real temp: "
                            + str(ctemp["temp"])
                        )
                        toggleRelay(allConfig["tpSockets"], member["members"], 1)
                    elif float(ctemp["temp"]) > (dtemp + 0.5):
                        print(
                            "Group: "
                            + member["groupname"]
                            + " temp to high: set temp: "
                            + str(dtemp).strip("\n")
                            + " real temp: "
                            + str(ctemp["temp"])
                        )
                        toggleRelay(allConfig["tpSockets"], member["members"], 0)
                    else:
                        print(
                            "Group: "
                            + member["groupname"]
                            + " temp within range: set temp: "
                            + str(dtemp).strip("\n")
                            + " real temp: "
                            + str(ctemp["temp"])
                        )
                    # toggleRelay(allConfig['tpSockets'],member['members'],0) # If within range, leave it
            else:
                #
                # Not controlled by sensor, flip to on if temp is set to high, flip off if temp is set to low
                #
                if currentTempSetting == "H":
                    print("Group: " + member["groupname"] + " set ON")
                    toggleRelay(allConfig["tpSockets"], member["members"], 1)
                else:
                    print("Group: " + member["groupname"] + " set OFF")
                    toggleRelay(allConfig["tpSockets"], member["members"], 0)
    #
    # Iterate over all group where inuse=Y again, to correct if backup exists
    #


"""
	for member in list(allConfig['groups']):
		#
		# Iterate through all current settings and fetch sensor temp value and desired temp
	 	#
	
		#
		#
		# Set temp if temp is sensor controlled
		# Pick backuptemp if temp == False
		# In range dtemp - 0.5 to dtemp 0.5 dont change setting If temp goes down keep of it temp raise keep on
		# if temp exceeds dtemp+0.5  turn off
		# if dtemp is below dtemp -0.5 turn on
		if member['inuse'] == 'Y' and member['usetermostat'] == 'Y':
				ctemp=currentTemp[member['groupname']]
				if ctemp is False:
					print("Severe error: temp not found for: "+member['groupname']+" "+allConfig['siteConfig'][member['sensorconfig']])
					ctemp=getBackupTemp(member['groupname'],currentTemp)
					if ctemp is False:
						print("Severe error: backuptemp not found for: "+member['groupname'])
					else:
						print('Using backuptemp for '+member['groupname'])
				if ctemp is False:
					return(False)
				
				if float(ctemp['temp'])<(dtemp-0.5):  # temp to low
					print("Group: "+member['groupname']+" temp to low: set temp: "+str(dtemp).strip('\n')+" real temp: "+str(ctemp['temp']))
					toggleRelay(allConfig['tpSockets'],member['members'],1)
				elif float(ctemp['temp'])>(dtemp+0.5):
					print("Group: "+member['groupname']+" temp to high: set temp: "+str(dtemp).strip('\n')+" real temp: "+str(ctemp['temp']))
					toggleRelay(allConfig['tpSockets'],member['members'],0)
				else:
					print("Group: "+member['groupname']+" temp within range: set temp: "+str(dtemp).strip('\n')+" real temp: "+str(ctemp['temp']))
		else:
			print("No termostat for group: "+member['groupname'])
"""


#
#  adjustTemp
#
#  Based on timeof day or later interface to Norpool, adjust temp
#
def adjustTemp(siteConfig, defaultTemp, adjustTemp):
    #
    # Read time of day
    #
    tz = pytz.timezone("Europe/Oslo")
    currentDateTime = datetime.now(tz)
    # If timeofday is between interval adjust temp
    #
    #  Currently not implemented, just use defaultTemp
    try:
        with open(siteConfig["elPriceFile"], "r") as infile:
            currPrice = json.load(infile)
    except:
        print("I/O Error when reading: " + siteConfig["elPriceFile"])
        #
        # norpool data not available
        #
        if (currentDateTime.hour > 6 and currentDateTime.hour < 11) or (
            currentDateTime.hour > 14 and currentDateTime.hour < 19
        ):
            print("Adjust temp on estimate")
            return adjustTemp
        else:
            return defaultTemp
    #
    # norpool net 24 hours are available
    #
    hourPrice = findHourPrice(currPrice, currentDateTime.hour)
    avgPrice = getAvgPrice(currPrice)
    print("CurrentPrice: " + str(hourPrice) + " Average Price: " + str(avgPrice))
    if hourPrice > avgPrice:
        print("Adjust based on norpool")
        return adjustTemp
    else:
        print("no norpool adjustment")
    return defaultTemp


#
#  backupTemp
#  backup for Gang == Stue
#  backup for Stue == gang
#
def getBackupTemp(groupName, currentTemp):
    if groupName == "Stue":
        return currentTemp["Gang"]
    elif groupName == "Gang":
        return currentTemp["Stue"]


def findHourPrice(dayPrices, hour):
    count = len(dayPrices)
    for i in range(0, count):
        sTime = dayPrices[i]["time_start"]
        eTime = dayPrices[i]["time_end"]
        startTime = datetime.strptime(sTime[:22] + sTime[23:], "%Y-%m-%dT%H:%M:%S%z")
        if hour == startTime.hour:
            break
    if i < count:
        return dayPrices[i]["NOK_per_kWh"]


def getAvgPrice(dayPrices):
    if dayPrices != False:
        #
        # Iterate over prices anc calculate todays avg price.
        #
        priceAcc = 0
        count = len(dayPrices)
        for i in range(0, count):
            priceAcc = priceAcc + dayPrices[i]["NOK_per_kWh"]
        avgPrice = priceAcc / count
        return avgPrice
    else:
        return False


#
# Main
#
def main():
    global siteConfigFile

    #
    # Identify program
    #
    print()
    print("Termostat V7 version: " + progVersion)
    print()
    #
    # process comand line onl one optin available, -f filename for sysconfig fiel
    #
    argsParser = argparse.ArgumentParser(description="Termostat program")
    argsParser.add_argument(
        "--configfile", default=siteConfigFile, type=str, help="Site Config File"
    )
    args = argsParser.parse_args()
    siteConfigFile = args.configfile

    #
    # Load static site config information
    #
    allConfig = load_site_config(siteConfigFile)
    if not allConfig:
        print("Error Loading confguration")
        return 1
    #
    # Fetch dynamic temp setting
    #
    print("Fetch dynamic temp setting")
    desiredTemp = getDesiredTempSetting(allConfig["siteConfig"]["tempSettingURL"])
    #
    # Save current desired temp values, to be consumed by other programs
    # Works as cache for the desired temp config
    #
    fp = open(allConfig["siteConfig"]["desiredtempfile"], "w")
    fp.write(json.dumps(desiredTemp))
    fp.close()
    #
    # Process termostat
    #
    print("Processing Termostat settings")
    termostat(allConfig, desiredTemp)
    #
    print("Termostat setting completed")


if __name__ == "__main__":
    main()
