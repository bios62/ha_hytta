import os
import time
import requests
import urllib3
import sqlite3
import json
import platform
import urllib.parse
from common import *

# from rpiglobals import rpiInitVariables
import argparse
import pytz
from datetime import datetime

#
#  Globals
#

defaultDebugFlag = 255
debugFlagCommon = 0
progVersion = "getprices 14122022"


def getstrom(url, priceArea, priceDate=None):
    if priceDate is None:
        tz = pytz.timezone("Europe/Oslo")
        currentDateTime = datetime.now(tz)
    else:
        currentDateTime = priceDate
    urlStr = (
        "%4d" % currentDateTime.year
        + "/"
        + "%02d" % currentDateTime.month
        + "-"
        + "%02d" % currentDateTime.day
        + "_"
        + priceArea
        + ".json"
    )
    headers = {"content-type": "application/json"}
    curlURL = url + urlStr
    r = requests.get(curlURL, headers=headers)
    printDebugCommon(r.status_code)
    if r.status_code > 201:
        print(r.text)
        print(r.status_code)
        return False
    else:
        try:
            return json.loads(r.text)
        except:
            print("El Prices not in proper JSON format")
            print(r.text)
            return False


def main():
    global debugFlagCommon
    global rpig

    print()
    print("elprice downloader version: " + progVersion)
    #
    # Get site config
    #
    if platform.system().lower() == "linux":
        siteConfigFile = "/home/pi/conf/siteconfig.json"
    else:
        siteConfigFile = "g:\\demo_projects\\pi\\hytta\\config.json"

    argsParser = argparse.ArgumentParser(description="Get EL Prices")
    argsParser.add_argument(
        "--configfile", default=siteConfigFile, type=str, help="Site Config File"
    )
    argsParser.add_argument("--debug", default=None, type=int, help="debug flag")
    args = argsParser.parse_args()
    siteConfigFile = args.configfile
    if args.debug is None:
        debugFlagCommon = defaultDebugFlag
    else:
        debugFlagCommon = args.debug
    #
    #  Load config file
    #
    configFileName = args.configfile
    if os.path.isfile(configFileName):
        siteConfig = rpiInitVariables(siteConfigFile)
    else:
        print("Config file does not exists")
        print("Exiting")
        return 1
    #
    # Get the prices
    #

    currPrice = getstrom(siteConfig.elPriceURL, siteConfig.elPriceArea)
    if currPrice != False:
        try:
            with open(siteConfig.elPriceFile, "w") as outfile:
                json.dump(currPrice, outfile)
        except IOError:
            print("I/O error writeing json result file file: " + elPriceFile)
            print("Existing")
            return 1
    else:
        print("Fetch of 24 hours ahead price failed")
        return 1
    print("New prices successfully saved")
    return 0


if __name__ == "__main__":
    main()
