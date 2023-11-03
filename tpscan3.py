# -*- coding: utf-8 -*-

import argparse
import socket
import sys
import json
import traceback

# from rpiglobals import rpiInitVariables
# from commonV2 import load_config_from_file

# import commonV2
from struct import pack
from pprint import pprint
from tplib3 import *
import platform

# tpscan
#
# Scans throug a given iprange is a given port is active
# Scans by trying HS100 status REST api call
# If a TCP connection and valid result is obtained, saves socket name and ip adress in file pointet to by siteconfig
#
# Python version: 3.x and above
#
# Modifictions
# 	5/8 - 20, uses standard siteconfig class rpglobals for site config
#   30/11 -20 switch to convention, termgroupmembers name matches device name. this is the name saved in socket file
#   14/8-23  Removed rpiglobals
#   14/8-23 modified to run on Py38, with tplib3.py
#
# Usage:
#
# python tpscan.py [--subnet subnet] [--ipstart start address] [--ipend stop adress inclusive] [--tpport port] [--resultfile filename]
#
# subnet given as start adress of net
#

scanVersion = "1.0 Alpha 140823"
debugFlag = 1

if platform.system().lower() == "linux":
    default_config_file = "/home/pi/conf/siteconfig.json"
else:
    default_config_file = "C:\\usr\\demo_projects\\pi\\hytta\\config.json"


def main():
    print("Tp Link socket scanner version: " + scanVersion)

    argsParser = argparse.ArgumentParser(description="TP Link port scanner")
    argsParser.add_argument(
        "--subnet",
        default="192.168.0.1",
        type=str,
        help="Enter Subnet base in form xxx.xxx.xxx.0",
    )
    argsParser.add_argument(
        "--ipstart", default=1, type=int, help="Start IP adress for scan"
    )
    argsParser.add_argument(
        "--ipend", default=255, type=int, help="End IP adress for scan"
    )
    argsParser.add_argument(
        "--tpport", default=9999, type=int, help="TP Link Port number"
    )
    argsParser.add_argument(
        "--resultfile", default=None, type=str, help="Temporary result file"
    )
    argsParser.add_argument(
        "--siteconfig",
        default=default_config_file,
        type=str,
        help="host style file with IP addresses",
    )
    args = argsParser.parse_args()
    #
    # site_config = load_config_from_file(args.siteconfig)
    # print(site_config)
    try:
        s = socket.inet_aton(args.subnet)
        scan(
            args.subnet,
            args.ipstart,
            args.ipend,
            args.tpport,
            args.resultfile,
        )
    except socket.error:
        print("")
        print("Incorrect subnet value added")
        print("")
        # sys.exit()


# def getName(ip,port):
def getName(tpsocket):
    cmd = '{"system":{"get_sysinfo":{}}}'
    """
    result=json.load(do_tplink(ip,cmd,port))
    res=result['system']['get_sysinfo']
    for line in res:
        print(line)
    """
    if debugFlag == 1:
        print(cmd)
    print(cmd)
    try:
        tpsocket.send(encrypt(cmd))
        dataFromDevice = tpsocket.recv(2048)
        result = json.loads(decrypt(dataFromDevice[4:]))
        print(result["system"]["get_sysinfo"]["alias"])
        return result["system"]["get_sysinfo"]["alias"]
    except socket.error:
        print("")
        print("Data send/read failed")
        print("")


def scan(subnet, ipstart, ipend, port, filename):
    try:
        fp = open(filename, "w")
        for i in range(ipstart, ipend + 1):
            octets = subnet.split(".")
            remoteIP = (
                octets[0] + "." + octets[1] + "." + octets[2] + "." + "{0:0d}".format(i)
            )
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # result = sock.connect_ex((remoteIP, port),2)
            print("trying: " + remoteIP)
            try:
                tpsocket = socket.create_connection((remoteIP, port), 2)
                newName = getName(tpsocket)
                # if newName.find(' ') >0:
                #    tpname=(newName).split(' ')[1]   # Fra gammel navnekonvensjon hytta socket, ny hytte_socketS
                # elif newName.find('_') >0:
                #    tpname=(newName).split('_')[1]
                # else:
                #    tpname=newName
                tpname = newName
                # fp.write(remoteIP+" "+tpname.replace(" ","_"))
                fp.write(remoteIP + " " + tpname + "\n")
                tpsocket.close()
            except socket.error:
                if debugFlag:
                    print("No server: " + remoteIP)
                pass
        fp.close()
    except Exception as e:
        print("Error in opening file: ", end="")
        print(filename)
        traceback.print_exc()


if __name__ == "__main__":
    main()
