import os
import glob
import time
import requests
import urllib3
import sqlite3
import json
import platform
import urllib.parse
from sqlite3 import Error
from tplib import *

# from rpiglobals import rpiInitVariables
from common import *
import argparse

# collector
#
# Collect all stats and updates iotlog table in desired cloud/database
# Collects, relays state of active relays, indoor temp in active zones, outdoor temp if available
##
# Python version: 3
#
# Modifictions
#   18/2  Something
# 	5/8-20 added save of desired temp in main
#   28/11-20 Changed to use socket/device name only no prefix
#   29/12-20 Extended colelction to include out door temp if it is not NULL (None) in the database
#   31/10-21  Added SODA Support
#   2/10-22  Made colelction more robust, swith to use sensorlib.py
#   4/12-22  Fixed minor bug in update to cloud for socket values. changed == 0 to == "1"
#   2/1-23  Changed report input format on JSON payload, SODA API
#   12/2-23  Disabled IP ipaddress 2.
#   14/2-23 removed need for rpiglobals, included in commonV2
#   14/2-23  Swicthed to tplib3, runs on python 3.
#   4/11-23  renamed to tplib when migrating to git and commonV2 to common
# Usage:
# python collector
#

progVersion = "2.0 140823"

#
# globals
#
# debug=True
# defaultdebug_flag=2+4+8+16+32
# defaultdebug_flag=127
defaultdebug_flag = 0
global debug_flag
# rpig = None

tplink_devices = {}


def print_result(temp_device, ip_address, result):
    print(
        "Device: "
        + temp_device
        + " IP Address: "
        + ip_address
        + " "
        + "Relay state: "
        + str(result["system"]["get_sysinfo"]["relay_state"])
    )


DBG0 = 0b00000000
DBG1 = 0b00000001
DBG2 = 0b00000010
DBG4 = 0b00000100
DBG8 = 0b00001000
DBG16 = 0b00010000
DBG32 = 0b00100000
DBG64 = 0b01000000


#
# Debug
# debug_flag == 2, debug gettemp operations
# debug_flag == 4, debug texternalipV2
# debug_flag == 8, debug main
# debug_flag == 16  saveSoda
# debug_flag == 32 save_property
#
def print_debug(text, dbg):
    global debug_flag
    if (debug_flag & dbg) > 0:
        print(text)


def getexternalip_NLU(site_config):
    # defining a params dict for the parameters to be sent to the API
    # PARAMS = {'siteid':'=hytta','propertyname':'=ip'}
    PARAMS = "siteid=hytta"
    # sending get request and saving the response as response object
    # r = requests.get(url = rpig.config["currentipURL"], params = PARAMS,verify=False)
    r = requests.get(url=site_config["currentipURL"], params=PARAMS, verify=False)
    if r:
        r.encoding = "utf-8"
        return r.text
    # extracting data in json format
    else:
        return "127.0.0.0"


def get_external_ip_V2(URL):
    #
    #  Fethc getmyip1URL
    #
    print_debug("Fetching externap IP from: " + URL, DBG4)
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )  # Disable SSL warnings
    headers = {"content-type": "application/json", "User-agent": "Mozilla/5.0"}
    r = False
    try:
        r = requests.get(url=URL, headers=headers, verify=False)
    except Exception as httpError:
        print("Error when fetching external IP (get_external_ip_V2):")
        print(httpError)
        r = False
    #
    # Evaluate result
    #
    if r:
        r.encoding = "utf-8"
        return r.text
    else:
        #
        # Clearly mark the IP as undefined
        #
        return False


#
#  Read the scoket config file
#  Iterate through all sockets and  fetch relay state
#  Externa script updates the socket config file with relay state
#
def collect_device(socketfile):
    # Read device IP addr
    fp = open(socketfile)
    line = fp.readline().strip("\n")
    info = '{"system":{"get_sysinfo":{}}}'
    # iterate through and verify temp
    results = dict()
    i = 1
    while line:
        if len(line) > 1:
            ipAddress = line.split(" ")[0]
            tempDevice = line.split(" ")[1]
            tpState = do_tplink(ipAddress, info, 9999, True)
            result = dict()
            result["device"] = tempDevice
            result["ipAddress"] = ipAddress
            result["relayState"] = str(tpState["system"]["get_sysinfo"]["relay_state"])
            results[str(i)] = result
            i = i + 1
        line = fp.readline().strip("\n")
    fp.close()

    return results


def collect(all_config, stats):
    #
    # Globals
    #
    #  Indor temp from DS1820, gang
    #
    #
    temp_stats = {}

    for member in list(all_config["groups"]):
        if member["inuse"] == "Y":
            print_debug("processing temp group: " + member["groupname"], DBG64)
            currentTemp = get_temp_for_group(
                all_config["siteConfig"],
                member,
                int(all_config["siteConfig"]["maxAgeInHours"]),
            )
            if not (currentTemp == False):
                temp_stats[member["groupname"]] = currentTemp
                print_debug(
                    "Grop: "
                    + member["groupname"]
                    + json.dumps(temp_stats[member["groupname"]]),
                    DBG64,
                )
            else:
                dummyTemp = {"temp": "-255", "time": "01/01/1970, 00:00:00"}
                temp_stats[member["groupname"]] = dummyTemp
                print_debug("Grop: " + member["groupname"] + " temp is False", DBG64)
    stats["tempStats"] = temp_stats
    #
    # Collect socket status
    #
    tp_states = collect_device(all_config["siteConfig"]["socketConfigFile"])
    stats["tpSockets"] = tp_states
    #
    # Get external IP
    #
    ip_stats = {}
    try:
        ip_stats["ipaddressFromCloud1"] = json.loads(
            get_external_ip_V2(all_config["getmyip1URL"])
        )
    except:
        ip_stats["ipaddressFromCloud1"] = json.loads(
            '{"currip":"1.1.1.1"}'
        )  # Somethin went wrong...
    """ # Disabled, not active
    try:
        ip_stats['ipaddressFromCloud2']=json.loads(getexternalipV2(all_config["getmyip2URL"]))
    except:
        ip_stats['ipaddressFromCloud2']=json.loads('{"currip":"1.1.1.1"}')  # Somethin went wrong..
    """
    stats["ipStats"] = ip_stats


def save_property(siteid, property_name, property_value, site_config):
    #
    # Globals
    #
    #
    # Saving to endpoint
    #
    # api-endpoint
    headers = {"content-type": "application/json"}
    # headers = {"content-type": "application/json", "Authorization": "<auth-key>" }
    payload = {}
    payload["siteid"] = siteid
    payload["logname"] = property_name
    payload["logvalue"] = property_value
    apiURL = site_config["iotstatsURL"]
    if (
        site_config["iotstatscloud"] == "iosp"
        or site_config["iotstatscloud"] == "apex-evry"
        or site_config["iotstatscloud"] == "iosjump"
    ):
        data = json.dumps(payload)
        r = requests.post(apiURL, headers=headers, data=data)
        print_debug(apiURL, DBG32)
        print_debug(headers, DBG32)
        print_debug(data, DBG32)
        print_debug(r.status_code, DBG32)
        if r.status_code > 201:
            print("Failed with Status code: " + str(r.status_code))
            print(apiURL)
            print("Payload: ")
            print(data)
        else:
            print_debug("Sucessfully saved property: " + str(r.status_code), DBG32)
            print(
                "Sucessfully saved property: "
                + property_name
                + " value: "
                + property_value
                + " http Status: "
                + str(r.status_code)
            )
    elif site_config["iotstatscloud"] == "one.com":  # Not maintained fro a while......
        apiURL += urllib.parse.urlencode(payload)
        r = requests.get(apiURL, headers=headers)
        print_debug(r.status_code, DBG32)
        if r.status_code > 200:
            print(r.text)
            print(r.status_code)


#
#  Save the data to a SODA structure in one REST call
#
def save_soda(stats, site_config):
    headers = {"content-type": "application/json", "Authorization": "<auth-key>"}
    data = json.dumps(stats)

    #
    #  Post payload with sodaURL
    #
    r = requests.post(
        site_config["sodaURL"],
        headers=headers,
        auth=(site_config["sodauser"], site_config["sodapwd"]),
        data=data,
    )
    print_debug(r.status_code, DBG16)
    if r.status_code > 201:
        print(r.text)
        print(r.status_code)
    else:
        print("SODA POST Success: ")
        print(str(r.text))


def main():
    global debug_flag
    # global rpig

    stats = {}
    print()
    print("Stats collector version: " + progVersion)
    #
    # Get site config
    #
    if platform.system().lower() == "linux":
        site_config_file = "/home/pi/conf/siteconfig.json"
    else:
        site_config_file = "g:\\demo_projects\\pi\\hytta\\config.json"

    args_parser = argparse.ArgumentParser(description="Collector program")
    args_parser.add_argument(
        "--configfile", default=site_config_file, type=str, help="Site Config File"
    )
    args_parser.add_argument("--debug", default=0, type=int, help="debug flag")
    args = args_parser.parse_args()
    site_config_file = args.configfile
    if args.debug == 0:
        debug_flag = defaultdebug_flag
    else:
        debug_flag = args.debug
    print("Debug:" + str(debug_flag))
    #
    #  Load config
    #
    all_config = load_site_config(site_config_file)
    # rpig=all_config['siteConfig']
    #
    # Print save URL
    #
    print()
    print("Saving properties to cloud: " + all_config["siteConfig"]["iotstatscloud"])
    collect(all_config, stats)
    print_debug("resultat: ", DBG8)
    print_debug(json.dumps(stats), DBG8)
    #
    # Current we have collected the follwing stats
    #
    #  Ipadress from two soruces
    #  temp from applicable sources
    #  tp sockets
    #  collected in the dictionary stats['temp_stats'],['ip_stats'],['tpsockets']
    #
    # process temp_stats
    #
    jsonStats = []
    print_debug(json.dumps(stats["tempStats"]), DBG8)
    for sensor_name in list(stats["tempStats"]):
        temp_values = stats["tempStats"][sensor_name]
        if not (stats["tempStats"][sensor_name] == False):
            print_debug(
                "name: "
                + sensor_name
                + " time: "
                + temp_values["time"]
                + " value: "
                + str(temp_values["temp"]),
                DBG8,
            )
            # save_property('hytta',sensor_name,stats['temp_stats'][sensor_name])
            save_property(
                "hytta",
                sensor_name,
                temp_values["time"] + ";" + str(temp_values["temp"]),
                all_config["siteConfig"],
            )
        else:
            print_debug("name: " + sensor_name + "is False", DBG8)

    for ip_name in list(stats["ipStats"]):
        ip_values = stats["ipStats"][ip_name]
        print_debug("name: " + ip_name + " " + "currip: " + ip_values["currip"], DBG8)
        save_property("hytta", ip_name, ip_values["currip"], all_config["siteConfig"])

    for device_name in list(stats["tpSockets"]):
        device = stats["tpSockets"][device_name]
        print_debug(
            "name: "
            + device["device"]
            + " ipaddress: "
            + device["ipAddress"]
            + " State: "
            + device["relayState"],
            DBG8,
        )
        save_property(
            "hytta",
            device["device"],
            ("ON " if device["relayState"] == "1" else "OFF"),
            all_config["siteConfig"],
        )

    #
    #  Upload to SODA API
    #  Basically copy everything, but coded in case a more selective upload is needed
    #
    jStats = {}
    jStats["sitename"] = "hytta"
    jStats["temp"] = stats["tempStats"]
    jStats["ipaddresses"] = stats["ipStats"]
    jStats["tpSockets"] = stats["tpSockets"]
    save_soda(jStats, all_config["siteConfig"])
    print_debug("*********************", DBG8)
    print_debug(json.dumps(stats), DBG8)
    print_debug("*********************", DBG8)


if __name__ == "__main__":
    main()
    # stats={}
    # stats["test1"]="15"
    # stats["test2"]=25
    # saveSoda(stats)
