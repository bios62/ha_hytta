Changelog
=========

2/1-24: removed py2 requirement

Connections
===========

Autonomous DB:

  ---------------------------------------------------------
  Usename   Password     Connect string   tenant
  --------- ------------ ---------------- -----------------
  iot       Mb450lclcl   Iosp\_low        Ios62
                                          
                                          Gmail/82Q\#\#\#
  ---------------------------------------------------------

Python2 in addition to python 3

Python3

sudo apt-get install python

python2
As of October 2023, Python2 is no longer required

curl [https://bootstrap.pypa.io/pip/2.7/get-pip.py --output
get-pip.py](https://bootstrap.pypa.io/pip/2.7/get-pip.py%20--output%20get-pip.py)

python2 get-pip.py

pip2 install virtualenv

sudo apt-get install python3

virtualenv -p /usr/bin/python2 tplink\_venv

## PIP Insalls 
pip install pytz

## OS INstall

sudo apt-get sshpass
vi /etc/hosts     add stue-pi



DS1820 temp sensor

1\. At the command prompt, enter sudo nano /boot/config.txt, then add
this to the bottom of the file:

dtoverlay=w1-gpio

2\. Exit Nano, and reboot the Pi with sudo reboot

3\. Log in to the Pi again, and at the command prompt enter 

sudo modprobe w1-gpio

4\. Then enter sudo modprobe w1-therm

https://www.circuitbasics.com/raspberry-pi-ds18b20-temperature-sensor-tutorial/
tmpfs /u01/iot tmpfs nodev,nosuid,size=1000M 0 0

mkdir -p /u01/iot
mount -a

Linux RAM Disk
==============
/etc/fstab

Data modell
===========

Configuration tables

CREATE TABLE "IOT"."TEMPGROUPMEMBERS"

( "TGMID" NUMBER(\*,0),

"GROUPID" NUMBER(\*,0),

"MEMBERNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

PRIMARY KEY ("TGMID")

CREATE TABLE "IOT"."TEMPGROUPS"

( "GROUPID" NUMBER(\*,0),

"GROUPNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"LOWTEMP" NUMBER(5,2),

"HIGHTEMP" NUMBER(5,2),

"SELECTEDTEMP" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"INUSE" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"SENSORTYPE" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

"SENSORCONFIG" VARCHAR2(100 BYTE) COLLATE "USING\_NLS\_COMP",

"USETERMOSTAT" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP",

"ADJUSTED\_LOW" NUMBER(7,2),

CONSTRAINT "CHK\_INUSE" CHECK (upper(inuse) in ('Y','N')) ENABLE,

CONSTRAINT "CHK\_SELECTEDTEMP" CHECK (upper(selectedtemp) in ('H','L'))
ENABLE,

PRIMARY KEY ("GROUPID")

Logging

CREATE TABLE "IOT"."IOTLOGS"

( "ID" NUMBER(\*,0) NOT NULL ENABLE,

"LOGNAME" VARCHAR2(100 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"LOGTIME" TIMESTAMP (6) DEFAULT CURRENT\_TIMESTAMP,

"SITEID" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"LOGVALUE" VARCHAR2(60 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

CONSTRAINT "IOTLOGS\_PK" PRIMARY KEY ("ID")

CREATE TABLE "IOT"."JIOTLOGS"

( "ID" VARCHAR2(255 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"CREATED\_ON" TIMESTAMP (6) DEFAULT sys\_extract\_utc(SYSTIMESTAMP) NOT
NULL ENABLE,

"LAST\_MODIFIED" TIMESTAMP (6) DEFAULT sys\_extract\_utc(SYSTIMESTAMP)
NOT NULL ENABLE,

"VERSION" VARCHAR2(255 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"JSON\_DOCUMENT" BLOB,

CHECK ("JSON\_DOCUMENT" is json format oson (size limit 32m)) ENABLE,

PRIMARY KEY ("ID")

CREATE TABLE "IOT"."TEMPGROUPMEMBERS"

( "TGMID" NUMBER(\*,0),

"GROUPID" NUMBER(\*,0),

"MEMBERNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

PRIMARY KEY ("TGMID")

CREATE TABLE "IOT"."TEMPGROUPS"

( "GROUPID" NUMBER(\*,0),

"GROUPNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"LOWTEMP" NUMBER(5,2),

"HIGHTEMP" NUMBER(5,2),

"SELECTEDTEMP" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"INUSE" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"SENSORTYPE" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

"SENSORCONFIG" VARCHAR2(100 BYTE) COLLATE "USING\_NLS\_COMP",

"USETERMOSTAT" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP",

"ADJUSTED\_LOW" NUMBER(7,2),

CONSTRAINT "CHK\_INUSE" CHECK (upper(inuse) in ('Y','N')) ENABLE,

CONSTRAINT "CHK\_SELECTEDTEMP" CHECK (upper(selectedtemp) in ('H','L'))
ENABLE,

PRIMARY KEY ("GROUPID")

Rest API
========

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  URL                                                    HTTP Method                    USAGE                                            SQL
  ------------------------------------------------------ ------------------------------ ------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  currentsetting/                                        GET                            Fetch current tempconfiguration setting          select groupname,lowtemp,hightemp,selectedtemp,nvl(adjusted\_low,lowtemp) adjustedtemp from tempgroups

  groupconfig/                                           GET                            Fetch current sensor configuration setting       select groupid,groupname,inuse,sensortype,sensorconfig,usetermostat,lowtemp,hightemp from tempgroups

  groupconfigall                                         GET                            NOT IN USE, replaced by currentsetting           select groupid,groupname,inuse,sensortype,sensorconfig,usetermostat,lowtemp,hightemp,selectedtemp from tempgroups

  Iotstats/                                              GET                            Fetch all stats for a site **In use????**        select l.logname name,l.logvalue value,l.logtime logtime from iotlogs l where l.siteid=:siteid and l.logtime = (select max(l2.logtime) from iotlogs l2 where l2.logname = l.logname)

  Iotstats/                                              POST                           Inserts one statistics                           declare
                                                                                                                                         
                                                         Payload:                                                                        id iotlogs.id%type;
                                                                                                                                         
                                                         {"siteid": "hytta",                                                             BEGIN
                                                                                                                                         
                                                         "logname": "hytte\_sov4",                                                       INSERT INTO iotlogs(logname, logtime, siteid, logvalue)
                                                                                                                                         
                                                         "logvalue": "OFF"}                                                              VALUES (:logname,sysdate,:siteid,:logvalue)
                                                                                                                                         
                                                                                                                                         RETURNING ID INTO id;
                                                                                                                                         
                                                                                                                                         :status := 201;
                                                                                                                                         
                                                                                                                                         END;

  Iotstats/:siteid                                       GET                            Fetch all stats for a site **In use????**        select l.logname name,l.logvalue value,to\_char(l.logtime,'DD/mm-yy hh24:mi:ss') logtime from iotlogs l where l.siteid=:siteid and l.logtime = (select max(l2.logtime) from iotlogs l2 where l2.logname = l.logname
                                                                                                                                         
                                                                                                                                         and l2.logtime&gt;(sysdate-(to\_number(to\_char(sysdate,'hh24'))/24)))

  members/                                               GET                            Fetch all members of a temp group, static info   select t.groupname,m.membername from tempgroups t,tempgroupmembers m where m.groupid=t.groupid

  setrange/                                              POST                           Updates static temp settings                     begin setrange(:groupname,:lowtemp,:hightemp,:p\_status);commit; end;
                                                                                                                                         
                                                         Payload: groupname,hightemp,                                                    
                                                                                                                                         
                                                         lowtemp                                                                         

  settemp/                                               POST                           Activates high or low temp, based on groupid     begin settemp(:groupid,:selectedtemp,:p\_status);commit; end;
                                                                                                                                         
                                                         Payload:                                                                        
                                                                                                                                         
                                                         Groupid, selectedtemp                                                           

  settempbyname/                                         POST                           Activates high or low temp, based on groupname   begin settempbyname(:groupname,:selectedtemp,:p\_status);commit; end;
                                                                                                                                         
                                                         Payload:                                                                        
                                                                                                                                         
                                                         Groupid, selectedtemp                                                           

  soda/latest/jiotlogs                                   POST                           Uploads collection of stats to json table        

  soda/latest/jiotlogs                                   PUT                            Creates JSON table                               

  https://revebaasen.no/php/saveipV3.php ?siteid=hytta   GET                            Saves current IP to one.com                      
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Scripts
=======

  /home/pi/scripts/getlocaltemp             Run as BASH., sudo to root to get access to devicefile. Calls /home/pi/python-scripts/getds1820.py
  ----------------------------------------- ------------------------------------------------------------------------------------------------------------------------
  /home/pi/scripts/saveip.bash              Saves current IP address to one.com rest API
  home/pi/scripts/getsocketIP.bash          Gets all status from all active tplink scokets and save in tplink socket file. Calls /home/pi/python-scripts/tpscan.py
  /home/pi/scripts/updategroupconfig.bash   Downloads all static group config from cloud via rest. Calls updategroupconfig.py
                                            

Cron Jobs
=========

4,9,14,19,24,29,34,39,44,49,54,59 \* \* \* \*
/home/pi/scripts/saveip.bash

\* \* \* \* \* bash /home/pi/scripts/getlocaltemp.bash

15,45 \* \* \* \* bash /home/pi/scripts/getsocketIP.bash

15,45 \* \* \* \* bash /home/pi/scripts/updategroupconfig.bash

\#3,18,33,48 \* \* \* \* date &gt;&gt;/home/pi/logs/tpstatus;bash
/home/pi/scripts/termostat.bash &gt;&gt;/home/pi/logs/tpstatus

\#15,45 \* \* \* \* /home/pi/scripts/wee\_start.sh
