--------------------------------------------------------
--  Procedure settemp
--------------------------------------------------------
create or replace procedure settemp ( p_groupid in integer, p_selectedtemp in varchar2, p_status out integer ) is
  antall integer;
  sqlerrtext varchar2(2000);
  sqlerrorcode integer;
begin
    --p_status:=200+p_groupid;
    p_status:=200;
    update tempgroups set selectedtemp=p_selectedtemp where groupid=p_groupid;
    select count(*) into antall from tempgroups where groupid=p_groupid;
    --insert into restlogs(apiname,logtext) values('settemp','Changed group id: '||to_char(p_groupid)||' '||p_selectedtemp||' Antall: '||to_char(antall));
    createrest_audit('settemp','Changed group id: '||to_char(p_groupid)||' '||p_selectedtemp||' Antall: '||to_char(antall));
	exception when others then
		p_status:=401;
        sqlerrtext:=sqlerrm;
        sqlerrorcode:=sqlcode;
        createrest_audit('settemp','ORA'||to_char(sqlerrorcode)||' '||substr(sqlerrtext,1,500));
    commit;
end;
--------------------------------------------------------
--  Procedure settempbyname
--------------------------------------------------------
create or replace procedure settempbyname ( p_groupname in varchar, p_selectedtemp in varchar2, p_status out integer ) is
begin
    p_status:=200;
    update tempgroups set selectedtemp=p_selectedtemp where lower(groupname)=lower(p_groupname);
	exception when others then
		p_status:=sqlcode;
end;

--------------------------------------------------------
--  Procedure setrange
--------------------------------------------------------
create or replace procedure setrange ( p_groupname in varchar, p_lowtemp in varchar2, p_hightemp in varchar2,p_status out integer ) is
begin
    p_status:=200;
    update tempgroups set lowtemp=p_lowtemp,hightemp=p_hightemp where lower(groupname)=lower(p_groupname);
	exception when others then
		p_status:=sqlcode;
end;
--------------------------------------------------------
--  Procedure createrest_audit
--------------------------------------------------------

create or replace procedure createrest_audit 
  ( p_apiname in varchar2, p_logtext in varchar2 ) as 
 PRAGMA AUTONOMOUS_TRANSACTION;
begin
  insert into restlogv2(apiname,logtext,logtime,ipaddress) values (p_apiname,p_logtext,sysdate,SYS_CONTEXT('USERENV','IP_ADDRESS'));
  commit;
end createrest_audit;
