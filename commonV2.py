import sqlite3
import time
import platform
import json
import os
import requests

# from rpiglobals import rpiInitVariables

#
#  Version: 14.08.2023
#
# Change 14/8-2023:  removed rpiglobals added load_config_from_file
#
# globals
#
DEBUG_FLAG_COMMON = 0
DBG0 = 0b00000000
DBG1 = 0b00000001
DBG2 = 0b00000010
DBG4 = 0b00000100
DBG8 = 0b00001000
DBG16 = 0b00010000
DBG32 = 0b00100000
DBG64 = 0b01000000

#
# List of mandatory parmeters
#
param_list = [
    "iotDirectory",
    "logDirectory",
    "weewxfile",
    "desiredtempfile",
    "remotetempfile",
    "localtempfile",
    "groupConfigFile",
    "socketConfigFile",
    "elPriceFile",
    "iotstatscloud",
    "iotstatsURL",
    "membersURL",
    "groupConfigURL",
    "tempSettingURL",
    "elPriceURL",
    "getmyip1URL",
    "getmyip2URL",
    "sodaURL",
    "elPriceArea",
    "sodauser",
    "sodapwd",
    "sodaURL",
    "elPriceArea",
    "maxAgeInHours",
]


#
#
class MissingConfigError(Exception):
    """Generic Exception for clean close of resoruces.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Value missing in configuration"):
        self.message = message
        super().__init__(self.message)


#
#
# Debug
# DEBUG_FLAG_COMMON == 2, debug print read_DS1820_json
# DEBUG_FLAG_COMMON == 4, debug print get_temp_for_group
#
def print_debug_common(text, dbg):
    if (DEBUG_FLAG_COMMON & dbg) > 0:
        print(text)


#
# verify_file_age()
#
# Verifies the age of the file, and if it is older than max_age_in_hours, return false
#
#  Convert to int and compare to 3600 sek * max_age_in_hours
#
def verify_file_age(file_name, max_age_in_hours):
    mod_time_since_epoc = int(os.path.getmtime(file_name))
    if int(time.time()) > mod_time_since_epoc + (max_age_in_hours * 3600):
        return False
    return True


#
#  Read DS1802 return lines
#
#  Verify Age of file,return False if to old
#  return False if any I/O error occurs
#
def read_DS1820_file(file_name, max_age_in_hours):
    try:
        if verify_file_age(file_name, max_age_in_hours) is False:
            print(
                "File: "
                + file_name
                + " is older than: "
                + str(max_age_in_hours)
                + " hours"
            )
            return False
        device_file = open(file_name, "r")
        lines = device_file.readlines()
        device_file.close()
        return lines
    except Exception as e:
        print("read_DS1820_file Error:")
        print(e)
        return False


#
#  read_DS1820_raw
#  Iterates max_loops time to attempt to fetch value
#
# !!!!! THE LOGIC HERE MUST BE WRONG
#
def read_DS1820_raw(site_config, group, max_loops, max_age_in_hours):
    loop_count = 0
    lines = False
    parameter_name = group["sensorconfig"]
    file_name = site_config[parameter_name]
    while (
        loop_count < max_loops
    ):  # Need to loop in case we are just in a sensor read cycle
        lines = read_DS1820_file(file_name, max_age_in_hours)
        if not lines:  # Max loops
            time.sleep(0.2)
            # lines = read_DS1820_file(file_name, max_age_in_hours)
            loop_count += 1
        elif lines[0].strip()[-3:] != "YES":  # File not ready
            time.sleep(0.2)
            # lines = read_DS1820_file(file_name, max_age_in_hours)
            loop_count += 1
        else:
            break
            #
            # If loop ends with cloopCount=20 we did not succseed in readin the file
            #
    if loop_count < max_loops:
        equal_pos = lines[1].find("t=")
        if equal_pos != -1:
            temp_string = lines[1][equal_pos + 2 :]
            temp_c = float(temp_string) / 1000.0
            return temp_c
        else:
            print(
                "getTempForGorup error: Group: "
                + group["groupName"]
                + " wrong format in file"
            )
            print(lines)
            return False
    else:
        print(
            "getTempForGorup error: Group: " + group["groupName"] + " File Read Error"
        )
        return False


#
#  Read DS1802 in json format
# Assumes external script (getds1820V2.py) is run by crontab
#
def read_DS1820_json(site_config, group, max_age_in_hours):
    print_debug_common("ds1820 debug", DBG2)
    print_debug_common(json.dumps(group), DBG2)
    parameter_name = group["sensorconfig"]
    file_name = site_config[parameter_name]
    print_debug_common(
        "file_name: " + file_name + " parameter Name: " + parameter_name, DBG2
    )
    #
    # Read the raw lines from file
    #
    lines = read_DS1820_file(file_name, max_age_in_hours)
    #
    # Parse JSON file
    #
    if lines is False:
        return False
    try:
        temp_json = json.loads(lines[0])
    except Exception as e:
        print("read_DS1820_json error:")
        print(e)
        return False
    return temp_json


#
#  Reading indoor temp from local Weewx sqlite database
#  inout 'indoor' or 'outdoor'
#
def read_weewx(site_config, group, inout):
    #
    # read from sqlite
    #
    conn = None
    #
    #  Set up a sqllite connection to a target
    #
    conn = create_connection(site_config[group["sensorconfig"]])
    if conn is False:
        print(
            "read_weewx error: Group: "
            + group["groupname"]
            + " could not open sqllite db"
        )
        return False  # Exit if connection fails
    #
    # Read the temp from the weewk db
    #

    cur = conn.cursor()
    if inout == "indoor":
        sqlstmt = "select ifnull(inTemp,-99),datetime from archive  where datetime="
        sqlstmt = sqlstmt + "(select max(datetime) from archive)"
    elif inout == "outdoor":
        sqlstmt = "select ifnull(outTemp,-99),datetime from archive  where datetime="
        sqlstmt = sqlstmt + "(select max(datetime) from archive)"
    else:
        print("Eror: read_weewx: inout paramter illeagl: " + str(inout))
        return False
    try:
        cur.execute(sqlstmt)
        rows = cur.fetchall()
        temp = {}
        temp["temp"] = ((rows[0])[0] - 32) / 1.8
        temp["time"] = rows[0][1]
    except Exception as sql_exception:
        print("SQL Statement failed: " + sqlstmt)
        print(str(sql_exception))
        return False
    return temp


def create_connection(db_file):
    """create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # print(sqlite3.version)
    except Exception as sqlite_error:
        print("sqllite open error:")
        print(sqlite_error)
        return False
    return conn


#
# Fetches the temp for a given group, from the sensors, based on groupname, and metdot/file
# ds1820 type devices read temp from line 2 of a specific file, temp is coded without .
#
# weewx reads from sqlite db
#
#  Caller is responsible for veriyfing that group is active
#
#  Return fetched temp in a dict as follows['sensorname']['time']['temp']
#  If temp reading for som reason is not possible, return False
#
def get_temp_for_group(site_config, group, max_file_age_in_hours):
    #
    # Local constants (to be moved to external config)
    #
    # Verify if inuse is set to Y
    #
    if group["inuse"] != "Y":
        print_debug_common(
            "getTempForGorup error: Group: "
            + group["groupname"]
            + " has not set inuse flag",
            DBG4,
        )
        return False
    #
    #  Split on sensor type
    #  ds1820 reads from a file
    #
    if group["sensortype"] == "ds1820":
        # ds1820 type, read from file
        max_loops = 20
        return read_DS1820_raw(site_config, group, max_loops, max_file_age_in_hours)
    elif group["sensortype"] == "weewx":
        return read_weewx(site_config, group, "indoor")
    elif group["sensortype"] == "weewx-outdoor":
        return read_weewx(site_config, group, "outdoor")
    elif group["sensortype"] == "json":
        return read_DS1820_json(site_config, group, max_file_age_in_hours)
    else:
        print("getTempForGorup error: Group: " + group["groupname"] + " not imlemented")
        return False
    return False


#
# load_config_from_file
#
#  Loads config, amd verifies mandatory parameters
#
#  Input parameter
#   site_config_file_name, full filepath to configfile
# Globals:
#   parameter_list, list of all mandatory parameters
# Output:
#   dict with all mandatory cnfig parameters
#
# Exception
#   throws configErrorException if mandatory parameter is missing
#
def load_config_from_file(site_config_file_name):
    config = {}

    # Open and process config file
    #
    try:
        fp = open(site_config_file_name, "r")
        params = json.loads(fp.read())
        fp.close()
    except Exception as e:
        print(" Process of config file failed")
        print(str(e))
        raise MissingConfigError("Processing of " + site_config_file_name + "failed")
    #
    config = {}
    # Iterate over all mandatory parameters
    for param_name in param_list:
        if param_name in params:
            config[param_name] = params[param_name]
        else:
            config[param_name] = None
            raise MissingConfigError(
                "Mandatory parameter: "
                + param_name
                + " Is not found in : "
                + site_config_file_name
            )
    return config


#
# get_groups
def get_groups(site_config):
    #
    #  Fetch all groups
    #
    headers = {"content-type": "application/json"}
    g = requests.get(site_config["groupConfigURL"], headers=headers)
    local_config = []
    if g.ok:
        #
        # Fetch memerships
        #
        m = requests.get(site_config["membersURL"], headers=headers)
        if m.ok:
            all_groups = g.json()["items"]
            all_members = m.json()["items"]
            #
            # Iterate through and add member array
            #
            for group in list(all_groups):
                #
                # iterate through all memers of a group
                #
                members = []
                for member in list(all_members):
                    if member["groupname"] == group["groupname"]:
                        members.append(member["membername"])
                group["members"] = members
                local_config.append(group)
            group_config_file_pointer = open(site_config["groupConfigFile"], "w")
            group_config_file_pointer.write(json.dumps(local_config))
            group_config_file_pointer.close()
            return local_config
        else:
            print("API call for members failed: " + str(m.status_code))
            return False
    else:
        print("API call for groups failed: " + str(g.status_code))
        return False


#
# Loads site local configuration
#
# loads group memer configuration from file, assumes changes are rare
# if the file is not found, loads from iot service
#
def load_site_config(site_config_file):
    #
    # Load master config file to get groupConfigFile path,
    # confURL, for static group membership
    # tempConfigURL for dynamic temp setting
    # groupconfig, contains statig gruop names and group sensor setup
    #
    all_config = {}
    # site_config = rpiInitVariables(site_configFile)
    site_config = load_config_from_file(site_config_file)

    # temp_setting_url = site_config["tempSettingURL"]
    group_config_file_name = site_config["groupConfigFile"]
    socket_config_file_name = site_config["socketConfigFile"]
    #
    # Load static membership,
    # if file exists, load local file
    # if not fetch form OT database
    #
    if os.path.isfile(group_config_file_name):
        try:
            config_file = open(group_config_file_name, "r")
            strconfig = config_file.read()
            groups = json.loads(strconfig)
            config_file.close()
        except IOError:
            print(
                "Member Config File"
                + group_config_file_name
                + " exists but is not accessible"
            )
            return False
    else:
        #
        # Group Config did not exists need to fetch it from iot database
        #
        groups = get_groups(site_config)
    #
    # Read the socket input file and add it to a dict
    # File is in host format  ip name
    # stored as an array  the config json
    all_sockets = []
    try:
        socket_file = open(socket_config_file_name)
        line = socket_file.readline().strip("\n")
        all_sockets = []
        while line:
            pos = line.find(" ")
            ip = line[:pos]
            host = line[pos + 1 :].lstrip()
            sockets = {}
            sockets["socketname"] = host
            sockets["ip"] = ip
            all_sockets.append(sockets)
            line = socket_file.readline().strip("\n")
    except IOError:
        print(
            "Socket Config File "
            + socket_config_file_name
            + " exists but is not accessible"
        )
        return False
    #
    # build dics result
    #

    all_config["groups"] = groups
    all_config["siteConfig"] = site_config
    all_config["tpSockets"] = all_sockets
    # all_config["rpig"] = site_config
    return all_config
