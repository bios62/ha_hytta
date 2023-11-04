import requests
import json
import sys
import urllib.parse
import os.path
import hashlib
import argparse

# import sqlite3
# from tplib3 import *
# import datetime
# import time
import platform

from sqlite3 import Error

# updategroupconfig
#
# Fetches siteconfig from config file
# fetches groupconfig from cloud
# fetches from disk
# if disk file is missing or there are changes, write new config to disk.
#
# Python version: 3
#
# Modifictions
# 	5/8-20 initial creation
#
# Usage:
# python updategroupconfig [--configfile filename]

progVersion = "1.0 05082020"

if platform.system().lower() == "linux":
    siteConfigFile = "/home/pi/conf/siteconfig.json"
else:
    siteConfigFile = "C:\\usr\\demo_projects\\pi\\hytta\\config.json"


def getGroups(siteConfig):
    #
    #  Fetch all groups
    #
    headers = {"content-type": "application/json"}
    try:
        g = requests.get(siteConfig["groupConfigURL"], headers=headers)
    except IOError as err:
        print("REST API Call for: " + siteConfig["groupConfigURL"] + " failed: ", err)
        return False
    localConfig = []
    if g.ok:
        #
        # Fetch memerships
        #
        try:
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
                print(
                    "API call for members failed, JSON Parse Error: "
                    + str(m.status_code)
                )
                return False
        except exception as e:
            print("API Call generated invalid result")
            print(siteConfig["membersURL"])
            print(headers)
            print(str(e))
            return False
    else:
        print("API call for groups failed: " + str(g.status_code))
        return False


#
def loadSiteConfig(siteConfigFile):
    #
    # Load master config file to get groupConfigFile path,
    # confURL, for static group membership
    # tempConfigURL for dynamic temp setting
    # groupconfig, contains statig gruop names and group sensor setup
    #
    try:
        f = open(siteConfigFile, "r")
        strsiteconfig = f.read()
        siteConfig = json.loads(strsiteconfig)
        f.close()
        return siteConfig
    except IOError:
        print("Site Config File" + siteConfigFile + " is not accessible")
        return False
    return null


def main():
    global siteConfigFile
    #
    # Identify program
    #
    print()
    print("update group config Version: " + progVersion)
    print()
    #
    # process comand line onl one optin available, -f filename for sysconfig fiel
    #
    argsParser = argparse.ArgumentParser(description="updategroupconfig program")
    argsParser.add_argument(
        "--configfile", default=siteConfigFile, type=str, help="Site Config File"
    )
    args = argsParser.parse_args()
    siteConfigFile = args.configfile
    #
    # Load static site config information
    #
    siteConfig = loadSiteConfig(siteConfigFile)
    if not siteConfig:
        print("Error Loading confguration")
        return 1
    #
    #  get current group config file
    #
    if os.path.isfile(siteConfig["groupConfigFile"]):
        try:
            f = open(siteConfig["groupConfigFile"], "r")
            strconfig = f.read()
            if len(strconfig) > 1:
                currentGroups = json.loads(strconfig)
            else:
                currentGroups = "{}"
            f.close()
        except IOError:
            print(
                "Member Config File"
                + siteConfig["groupConfigFile"]
                + " exists but is not accessible"
            )
            return 2
        groups = getGroups(siteConfig)
        if groups != False:
            if (
                hashlib.md5(json.dumps(groups).encode("utf-8")).digest()
                != hashlib.md5(json.dumps(currentGroups).encode("utf-8")).digest()
            ):
                print("New version found, saving.....")
                f = open(siteConfig["groupConfigFile"], "w")
                f.write(json.dumps(groups))
                f.close()
            else:
                print("Files are in sync")
            sys.exit(0)
        else:
            print("getGroups failed")
            sys.exit(1)
        sys.exit(2)
    else:
        #
        # Group Config did not exists need to fetch it from iot database
        #
        groups = getGroups(siteConfig)

    print("groupconfig.json synchronized")


if __name__ == "__main__":
    main()
