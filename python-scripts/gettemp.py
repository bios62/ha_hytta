import sqlite3
from sqlite3 import Error

# Changed from tplib to tplib3 to be Py 3 compatilble 5/11-2023
from tplib3 import *


def create_connection(db_file):
    """create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # print(sqlite3.version)
    except Error as e:
        print(e)
    return conn


def gettemp_from_weewx(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    sqlstmt = "select inTemp,outTemp,datetime from archive  where datetime="
    sqlstmt = sqlstmt + "(select max(datetime) from archive)"
    cur.execute(sqlstmt)
    rows = cur.fetchall()
    #        print (type(rows[0]))

    # 	for row in rows:
    # 		print(row)
    inTemp = ((rows[0])[0] - 32) / 1.8
    return inTemp


def read_temp_target(filename):
    try:
        with open(filename, "r") as f:
            tempTarget = f.readline()
        return tempTarget
    except Exception:
        return 5


def main():
    database = "/var/lib/weewx/weewx.sdb"
    onsw = '{"system":{"set_relay_state":{"state":1}}}'
    offsw = '{"system":{"set_relay_state":{"state":0}}}'
    # create a database connection
    conn = create_connection(database)
    with conn:
        currTemp = gettemp_from_weewx(conn)
        # 		destTemp=read_temp_target(filename)
        # 		if(destTemp>currTemp) :
        print("temperaturen er: " + str(currTemp))


if __name__ == "__main__":
    main()
