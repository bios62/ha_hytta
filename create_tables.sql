--------------------------------------------------------
--  Drop all tables
--------------------------------------------------------
drop table iotlogs;
drop table jiotlogs;
drop table "TEMPGROUPMEMBERS";
drop table "TEMPGROUPS";


--------------------------------------------------------
--  Create table IOTLOGS
--------------------------------------------------------
CREATE TABLE "IOTLOGS" (
  "ID" NUMBER(*,0), "LOGNAME" VARCHAR2(100), "LOGTIME" TIMESTAMP (6) DEFAULT CURRENT_TIMESTAMP, "SITEID" VARCHAR2(20), "LOGVALUE" VARCHAR2(60)
  ) ;

--------------------------------------------------------
--  Create table IOTLOGS
--------------------------------------------------------

CREATE TABLE "JIOTLOGS" (
  "ID" VARCHAR2(255), "CREATED_ON" TIMESTAMP (6) DEFAULT sys_extract_utc(SYSTIMESTAMP), "LAST_MODIFIED" TIMESTAMP (6) DEFAULT sys_extract_utc(SYSTIMESTAMP), "VERSION" VARCHAR2(255), "JSON_DOCUMENT" BLOB
  ) ;

--------------------------------------------------------
--  Create table IOTLOGS
--------------------------------------------------------

CREATE TABLE "TEMPGROUPMEMBERS" (
  "TGMID" NUMBER(*,0), "GROUPID" NUMBER(*,0), "MEMBERNAME" VARCHAR2(20)
  ) ;

--------------------------------------------------------
--  Create table IOTLOGS
--------------------------------------------------------

CREATE TABLE "TEMPGROUPS" (
  "GROUPID" NUMBER(*,0), "GROUPNAME" VARCHAR2(20), "LOWTEMP" NUMBER(5,2), "HIGHTEMP" NUMBER(5,2), "SELECTEDTEMP" VARCHAR2(1), "INUSE" VARCHAR2(1), 
  "SENSORTYPE" VARCHAR2(20), "SENSORCONFIG" VARCHAR2(100), "USETERMOSTAT" VARCHAR2(1), "ADJUSTED_LOW" NUMBER(7,2), "BACKUPSENSOR" NUMBER
  ) ;

--------------------------------------------------------
--  Create view IOTVALUESTATS
--------------------------------------------------------

CREATE OR REPLACE FORCE EDITIONABLE VIEW "IOTVALUESTATS" (
  "NAME", "VALUE", "LOGTIME", "SITEID") AS (select l.logname name,l.logvalue value,l.logtime logtime, 
  l.siteid siteid from iotlogs  l where l.logtime = (select max(l2.logtime) from iotlogs l2 where l2.logname = l.logname)
  );

--------------------------------------------------------
--  Unique Indexes
--------------------------------------------------------
CREATE UNIQUE INDEX "IOTLOGS_PK" ON "IOTLOGS" ("ID") ;
CREATE UNIQUE INDEX "SYS_C0057933" ON "JIOTLOGS" ("ID") ;
CREATE UNIQUE INDEX "SYS_C0057944" ON "TEMPGROUPMEMBERS" ("TGMID") ;
CREATE UNIQUE INDEX "SYS_C0057942" ON "TEMPGROUPS" ("GROUPID") ;
CREATE OR REPLACE EDITIONABLE TRIGGER "IOTLOGSTRG" 

--------------------------------------------------------
--  Constraints for Trigger for IOTLOGS
--------------------------------------------------------

BEFORE INSERT ON iotlogs
FOR EACH ROW
   WHEN (new.ID IS NULL) BEGIN
  :new.ID := iotlogsseq.NEXTVAL;
  if(:new.logtime is NULL) then
    :new.logtime:=systimestamp;
  end if;
END;
/
ALTER TRIGGER "IOTLOGSTRG" ENABLE;

--------------------------------------------------------
--  Constraints for Table IOTLOGS
--------------------------------------------------------

ALTER TABLE "IOTLOGS" MODIFY ("ID" NOT NULL ENABLE);
ALTER TABLE "IOTLOGS" MODIFY ("LOGNAME" NOT NULL ENABLE);
ALTER TABLE "IOTLOGS" MODIFY ("SITEID" NOT NULL ENABLE);
ALTER TABLE "IOTLOGS" MODIFY ("LOGVALUE" NOT NULL ENABLE);
ALTER TABLE "IOTLOGS" ADD CONSTRAINT "IOTLOGS_PK" PRIMARY KEY ("ID") USING INDEX  ENABLE;

--------------------------------------------------------
--  Constraints for Table JIOTLOGS
--------------------------------------------------------

ALTER TABLE "JIOTLOGS" MODIFY ("ID" NOT NULL ENABLE);
ALTER TABLE "JIOTLOGS" MODIFY ("CREATED_ON" NOT NULL ENABLE);
ALTER TABLE "JIOTLOGS" MODIFY ("LAST_MODIFIED" NOT NULL ENABLE);
ALTER TABLE "JIOTLOGS" MODIFY ("VERSION" NOT NULL ENABLE);
ALTER TABLE "JIOTLOGS" ADD CHECK ("JSON_DOCUMENT" is json format oson (size limit 32m)) ENABLE;
ALTER TABLE "JIOTLOGS" ADD PRIMARY KEY ("ID") USING INDEX  ENABLE;

--------------------------------------------------------
--  Constraints for Table TEMPGROUPMEMBERS
--------------------------------------------------------

ALTER TABLE "TEMPGROUPMEMBERS" ADD PRIMARY KEY ("TGMID") USING INDEX  ENABLE;


--------------------------------------------------------
--  Constraints for Table TEMPGROUPS
--------------------------------------------------------

ALTER TABLE "TEMPGROUPS" MODIFY ("GROUPNAME" NOT NULL ENABLE);
ALTER TABLE "TEMPGROUPS" MODIFY ("SELECTEDTEMP" NOT NULL ENABLE);
ALTER TABLE "TEMPGROUPS" MODIFY ("INUSE" NOT NULL ENABLE);
ALTER TABLE "TEMPGROUPS" ADD CONSTRAINT "CHK_INUSE" CHECK (upper(inuse) in ('Y','N')) ENABLE;
ALTER TABLE "TEMPGROUPS" ADD CONSTRAINT "CHK_SELECTEDTEMP" CHECK (upper(selectedtemp) in ('H','L')) ENABLE;
ALTER TABLE "TEMPGROUPS" ADD PRIMARY KEY ("GROUPID") USING INDEX  ENABLE;

--------------------------------------------------------
--  Ref Constraints for Table TEMPGROUPMEMBERS
--------------------------------------------------------

ALTER TABLE "TEMPGROUPMEMBERS" ADD CONSTRAINT "FK_TGROUPS" FOREIGN KEY ("GROUPID") REFERENCES "TEMPGROUPS" ("GROUPID") ENABLE;

--- END --------------------------------------------------------------------


