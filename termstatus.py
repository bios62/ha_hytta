import sqlite3
from sqlite3 import Error
from tplib import *
import datetime

"""
Globals
"""
from rpiglobals import rpiInitVariables
outdoorTemp=-50
rpig=rpiInitVariables()

#
# Last modfified 4/8-2020. Changed to use rpiglobals for all settings
#                          Changed to use files copied by cronscript with jsonformat for ds1820 remote and local
#
# Program that reads the 3 temp sources, weexw, local DS1820 and remote DS1820
#
# Python 2.7

progVersion="1.101219"
 
def create_connection(db_file):
	""" create a database connection to a SQLite database """
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)
	return conn

def gettemp_from_weewx(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    global outdoorTemp
    outdoorTemp=(-50)
    cur = conn.cursor()
    sqlstmt="select inTemp,ifnull(outTemp,-22),datetime from archive  where datetime="
    sqlstmt=sqlstmt+"(select max(datetime) from archive)"
    cur.execute(sqlstmt)
 
    rows = cur.fetchall()
#        print (type(rows[0]))
 
#	for row in rows:
#		print(row)
    inTemp=((rows[0])[0]-32)/1.8
    if(((rows[0])[1]) != -22):
        outdoorTemp=((rows[0])[1]-32)/1.8
    else:
        outdoorTemp=-60
    return(inTemp)
#
# Read local copies of ds1820
# based on filename
def read_ds1820(tempFile):
    fp=open(tempFile,"r")
    tempData=json.loads(fp.read())
    fp.close()
    return(tempData)


def printResult(tempDevice,ipAddress,result):
    
#    for line in result:
#        if(line.find("alias")>=0 or line.find("relay_state")>=0 or line.find("err_code")>=0):
#            print(line)

    #print(result)
    print("Device: "+tempDevice+" IP Address: "+ipAddress+" "+"Relay state: "+str(result["system"]["get_sysinfo"]["relay_state"]))

	
def main():
    
    global outdoorTemp
    
    database = rpig.weewxfile
    onsw='{"system":{"set_relay_state":{"state":1}}}'
    offsw= '{"system":{"set_relay_state":{"state":0}}}'
    info='{"system":{"get_sysinfo":{}}}'
    
    argsParser=argparse.ArgumentParser(description='Temperature and device status')
    argsParser.add_argument("--sone",default="gang",type=str,help="Sone, gang, stue")
    argsParser.add_argument("--targetfile",default=rpig.targetfile,type=str,help="Filnavn med target temp for sone")
    args=argsParser.parse_args()
    tempDevice=args.sone
    filename=args.targetfile
    
    print("  Temp Status version: "+progVersion+" "+datetime.datetime.now().strftime("%d/%m-%Y %H:%M:%S"))
# create a database connection
    conn = create_connection(database)
    currTemp=gettemp_from_weewx(conn)
# Read desired temp
    destTemp=read_temp_target(filename)
    print("  Outdoor temp: "+str(outdoorTemp)+" Indoor temp: "+str(currTemp)+" Desired indoor temp: "+destTemp)
# Read device IP addr
    
    fp=open(tpsocketfile)

    line=fp.readline().strip('\n')
    #line=fp.readline();
    
# iterate through and verify relay state
    
    while (line):
        ipAddress=line.split(' ')[0]
        tempDevice=line.split(' ')[1]
        result=do_tplink(ipAddress,info,9999,True)
        printResult(tempDevice,ipAddress,result)
        line=fp.readline().strip('\n');
    fp.close()
         
if __name__ == '__main__':
    main()
