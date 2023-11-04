<?php
//
// Last updated 30/8-2020
//
// two zones conains all data, "gang" and "stue" other zones ma only show socket value and 
// are able to flip the value Special case hytte_stue3 should ave it own zone definition
//
//
// Debugflag =2 prints REST exec time
//
//  Gjøre om rooms til liste av rom med tempsoner, med tilhørende navn på sensor, bli kbitt dobbelt kode
//  bruke activezones, til å displaye data 
// lage array med zone have temp
// Skrive mer generisk
//
// 16/9-21
// Feil i initipagev2, den får ikke med settings, bruker feil rest kall i php kode. currentsettings er ikke tatt i bruke
//
//  Endret til å bruke always free iosp-iot bruker med ny URLK over https
//
   $DEBUGFLAG=0;
   $RESTSERVER="ios62";
   //$activeSones=array('Stue','Gang','Sov'); # Now fetched from REST API
   if(isset($_GET['dbg'])){
     $DEBUGFLAG=$_GET['dbg'];
   }
   $Advanced=false;
   if(isset($_GET['advanced'])){
    $Advanced=true;
  }
   if ( $RESTSERVER == "OCILBR") {
       $ordsServer="138.3.241.22";  // oraemeasec LBR
       $iotlogurl="http://".$ordsServer."/ords/iot/iotv1/iotstats/hytta";
       $membersurl="http://".$ordsServer."/ords/iot/iotv1/members/";
       $groupsurl="http://".$ordsServer."/ords/iot/iotv1/groupconfigall";
       $settempurl="http://".$ordsServer."/ords/iot/iotv1/settempbyname/";
       $setrangeurl="https://".$ordsServer."/ords/iot/iotv1/setrange/";
   } else if ( $RESTSERVER == "ios62") {
   // For Always free usage
      $ordsServer="tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1.oraclecloudapps.com";
      $iotlogurl="https://".$ordsServer."/ords/iot/iotv1/iotstats/hytta";
      $membersurl="https://".$ordsServer."/ords/iot/iotv1/members/";
      $groupsurl="https://".$ordsServer."/ords/iot/iotv1/groupconfigall";
      $settempurl="https://".$ordsServer."/ords/iot/iotv1/settempbyname/";
      $setrangeurl="https://".$ordsServer."/ords/iot/iotv1/setrange/";
   }
   //
   //  Fetch all groups
   //
   $milliseconds = round(microtime(true) * 1000);
   $ch = curl_init(); 
   curl_setopt($ch, CURLOPT_URL, $groupsurl); 
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 
   curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
   $apiResponse=curl_exec($ch);
   $exectime=round(microtime(true) * 1000) - $milliseconds;
   if($DEBUGFLAG == 2) {
       echo "<script> console.log(' groups exectime: ".$exectime."')</script>";
   }

   if(curl_error($ch)){
      $fp = fopen("curl_error.log", "wa");
      fwrite($fp, curl_error($ch));
      fclose($fp);
      echo "<script> window.alert('Feil: feilkode 100 (groupsinfo)');</script>";
   }
   $zones=[];
   $zoneList=[];   // Array contains list of zones

   $groups = (json_decode($apiResponse, true))['items'];  
   $groupString= $apiResponse; // For transfer to javascript

   //
   // itertrate through the group an build the group list
   //
   $timeState=[];
   $tempState=[];
   $adjustedTemp=[];
   for ($i=0;$i<count($groups);$i++) {
   //
   // Only active groups is to be added 
   //
       if ($groups[$i]['inuse'] == 'Y') {
           $zoneList[]=$groups[$i]['groupname'];
           //
           // Prefill values of time and temp
           //
           $timeState[$groups[$i]['groupname']]=NULL;
           $tempState[$groups[$i]['groupname']]=NULL;
           //$adjustedTemp[$groups[$i]['groupname']]=$groups[$i]['groupname']['adjustedtemp'];
       }
   }
   //
   // Fetch all  members
   //
   $milliseconds = round(microtime(true) * 1000);
   $ch = curl_init(); 
   curl_setopt($ch, CURLOPT_URL, $membersurl); 
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 
   curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
   $apiResponse=curl_exec($ch);
   $exectime=round(microtime(true) * 1000) - $milliseconds;
   if($DEBUGFLAG == 2) {
       echo "<script> console.log(' members exectime: ".$exectime."')</script>";
   }

   if(curl_error($ch)){
      $fp = fopen("curl_error.log", "wa");
      fwrite($fp, curl_error($ch));
      fclose($fp);
      echo "<script> window.alert('Feil: feilkode 101 (Memberinfo)');</script>";
   }
   $memberRecords = (json_decode($apiResponse, true))['items'];   
   //for ($i=0;$i<count($memberRecords);$i++){
   //    $zones[$memberRecords[$i]['groupname']][]=$memberRecords[$i]['membername'];
   //} 
   //
   // rooms to be processed
   //
   $rooms=$zoneList;
   //
   // Fethcstate form iottables
   //
   $milliseconds = round(microtime(true) * 1000);
   $ch = curl_init(); 
   curl_setopt($ch, CURLOPT_URL, $iotlogurl); 
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 
   curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
   $apiResponse=curl_exec($ch);
   $exectime=round(microtime(true) * 1000) - $milliseconds;
   if($DEBUGFLAG == 2) {
       echo "<script> console.log(' iotstats exectime: ".$exectime."')</script>";
   }

   if(curl_error($ch)){
      $fp = fopen("curl_error.log", "wa");
      fwrite($fp, curl_error($ch));
      fclose($fp);
   } else {
      $records = (json_decode($apiResponse, true))['items'];
      //$sockets=["gang" => "-","stue1"=>"-","stue2"=>"-","stue3"=>"-"];
      $sockets=[];    // Plain list of all sockets and their state
      $ipAdressPi="0.0.0.0";
	  $ipAdressPi1="1.1.1.1";
	  $ipAdressPi2="2.2.2.2";
      for($i=0;$i<count($records);$i++) {    
          //
          // TO be rewritten to match the sensors from the groups
          //
          $explodechar=";";
          if ($records[$i]["name"] == "Gang") {  // Active sensor is DS1820-gang ikke weex
                $timeState['Gang']=$records[$i]['logtime'];
                $ds1820=explode($explodechar,$records[$i]["value"]);
                $tempState['Gang']=round($ds1820[1]*1.0,1);
          } elseif ($records[$i]['name'] == 'Stue') {
            $timeState['Stue']=$records[$i]['logtime'];
            $ds1820=explode($explodechar,$records[$i]["value"]);
            $tempState['Stue']=round($ds1820[1]*1.0,1);

		  } elseif ($records[$i]['name'] == 'ipaddressFromCloud1') {
            $ipAdressPi1=$records[$i]['value'];
		  } elseif ($records[$i]['name'] == 'ipaddressFromCloud2') {
            $ipAdressPi2=$records[$i]['value'];
          } else {
          //
          // Gather socket values in sockets array
          //  
            $pos=strpos($records[$i]['name'],"hytte_");
            if ($pos === 0 or $pos >0 ) {
                if(strlen($records[$i]['name'])>6) {    // Length of hytte_
                    //$socket=substr($records[$i]['name'],$pos+6);

                    $socket=$records[$i]['name'];

                    if (rtrim($records[$i]['value']) == "ON")  {
                        $sockets[$socket]="På";
                    } else if (rtrim($records[$i]['value']) == "OFF")  {
                        $sockets[$socket]="Av";
                    } else {
                        $sockets[$socket]=$records[$i]['value'];
                    }
                }
            }
          }
      }
      //
      // The array sockets contain all recorded sockets
      // Need to match between groups and state
      //
      // Iterate over all groups and then match sockets to groups
      //
      ksort($sockets);
      $socketsState=[];
      foreach ($sockets as $socketName =>$state)  // 
      {
        // Iterate over sockets and find all sockets that is a member of this gorup
         foreach ($memberRecords as $member) {
            if($member['membername'] == $socketName ) {
               if(!isset($socketsState[$member['groupname']])) {
                $socketsState[$member['groupname']]=$state;
               } else {
                $socketsState[$member['groupname']]=$socketsState[$member['groupname']]."/".$state;
               }
               break;
            } 
          }    
      }
   }
   curl_close($ch);
   //echo "<br>".."<br>";
      
?>
<!DOCTYPE html>
<html>
<!--  Updated 30/8-2020 -->
   <head>
   <link rel="stylesheet" type="text/css" href="varme.css">
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
   <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
   <?php
   //
   // Need to add call to http://iosjump:8080/ords/iot/iotv1/groupconfig/ to get active/disabled zones
   //
     echo "<script>";
     $jszonelist="var zones=[";
     //for($i=0;$i<count($activeSones);$i++) {
        for($i=0;$i<count($zoneList);$i++) {
        $jszonelist=$jszonelist."'".$zoneList[$i]."'";
        if($i < (count($zoneList)-1)) {
            $jszonelist=$jszonelist.",";
        }
     }
     $jszonelist=$jszonelist."];";
     echo "</script>";
    echo "<script>";
     echo "$jszonelist";
     echo "var iosdbg='".$DEBUGFLAG."';";
     //echo "ordsServer='".$ordsServer."';";
     echo "settempurl='".$settempurl."';";
     echo "setrangeurl='".$setrangeurl."';";
	 $grps=json_encode($groups);
     echo "groupString='".json_encode($groups)."';";
     echo "</script>";
    ?>
    <script>
      function initPageV2() {  // Rewritten to consume data from PHP, reduce the amount of APi calls from  front end
          //
          // Fetch currect status of all zones
          //
                result=JSON.parse(groupString);
				printDebug("Groupstring: "+groupString);
                var item;
            

                for (i=0;i<result.length;i++) {
                    item=result[i];
                    //
                    // If the zone is in the active zones list set the current high/low value
                    //
					
                    if (typeof(zones.find(checkZone,item.groupname)) != "undefined") {
						printDebug("getting value for group: "+item.groupname);
                        if(item.selectedtemp == "H") {
                            currentState=true;
                        } else {
                            currentState=false;
                        }
                        printDebug("Lookup: "+item.groupname+" "+currentState);
                        cbElement=document.getElementById("cb"+item.groupname);  // If a button does not exists like weewx gang
                        if (!(cbElement === null)) {
                            cbElement.checked = currentState;
                            if(item.usetermostat == 'Y') {
                                document.getElementById("l"+item.groupname).value = item.lowtemp;
                                document.getElementById("h"+item.groupname).value = item.hightemp;
                            }
                            printDebug("Active "+item.groupname+" "+currentState);
                            printDebug("low value "+item.groupname+" "+item.lowtemp);
                            printDebug("high value "+item.groupname+" "+item.hightemp);
                            printDebug("use termostat "+item.groupname+" "+item.usetermostat);
                        } else {
                            printDebug("Element: cb"+item.groupname+" Does not exixst");
                        }
                    } else {
                        printDebug("Not active "+item.groupname);
						console.log("getting value for group: "+item.groupname);
                    }
                }
      }

      function printDebug(text)
      {
          if(iosdbg>0) {
              console.log(text);
          }
      }
      function setTermostat(name,newValue)
      {
        var postData={};
        if (newValue) {  // flip state  {"groupname":"Stue","selectedtemp":"H"}
            postData={groupname:name,selectedtemp:"H"};
        } else {
            postData={groupname:name,selectedtemp:"L"};
        }
        $.ajax({
              url: settempurl,
             type: "POST",
            dataType : "json",
            contentType: "application/json; charset=utf-8",
            data : JSON.stringify(postData),
              success: function(result) {
                printDebug("Updated "+name+" "+JSON.stringify(postData));
                printDebug(result);
               
          }, // success
          error: function(error,xhr) {
            printDebug('url: '+settempurl);
            printDebug('Data: '+postData);
            printDebug(xhr.status);
            printDebug(xhr.responseText);
            alert('Beklager, oppdateringen gikk feil');
          }  // error
        }); 
    }

    function checkZone(name) {
        return name == this;
    }

    function setCBValue(bname) {
        state=document.getElementById("cb"+bname).checked;
        printDebug("setter termostat til"+bname+" "+state);
        setTermostat(bname,state)
    }
    function setLimits() {
        iosdbg=1;
        //
        // Iterate over groups and set new values
        //
        
        for(i=0;i<zones.length;i++) {
            // Only "Stue" and "Gang" can be set
            if(zones[i] =="Stue" || zones[i] == "Gang") {
            newlowtemp=document.getElementById("l"+zones[i]).value;
            newhightemp=document.getElementById("h"+zones[i]).value;
            printDebug("Value of Low field: "+newlowtemp);
            printDebug("Value of High field: "+newhightemp);
            postData={groupname:zones[i],lowtemp:newlowtemp,hightemp:newhightemp};
            printDebug("payload: "+JSON.stringify(postData));
            $.ajax({
                  //url: "http://"+ordsServer+"/ords/iot/iotv1/setrange/",
                  url: setrangeurl,
                 type: "POST",
                dataType : "json",
                contentType: "application/json; charset=utf-8",
                data : JSON.stringify(postData),
                  success: function(result) {
                    printDebug("Updated "+name+" "+JSON.stringify(postData));
                    printDebug(result);
                  }, // success
                  error: function(error,xhr) {
                    alert('Beklager, oppdateringen gikk feil');
                    printDebug(xhr.status);
                    printDebug(xhr.responseText);
          }  // error
            });
            }
        }
        window.alert('Termostatens grenseverdier er oppdatert');
    }

    

    function trimNumber(num, len) {
    const modulu_one = 1;
    const start_numbers_float=2;
    var int_part = Math.trunc(num);
    var float_part = String(num % modulu_one);
        float_part = float_part.slice(start_numbers_float, start_numbers_float+len);
    return int_part+'.'+float_part;
    }


    // 
    // depreciated
    // initialzed from php
    // Kept as an example code, but not used
    //
    function getTempFromIOTCloud_NLIU()
    {
        return(0);  // Depreciated
        $.ajax({          
            url: "http://"+ordsServer+"/ords/iot/iotv1/iotstats/hytta",
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(result,status,xhr) {
                // Hardcoded mess as no zones is done in the same way
                for(i=0; i < result.items.length;i++) {
                    printDebug("Current iotlog"+result.items[i].name);
                    if (result.items[i].name == "gangWeewx") {
                        tempGang=trimNumber(result.items[i].value,1);
                        timeGang=result.items[i].logtime;
                        printDebug("Current temp Gang"+timeGang+" "+tempGang);
                        var node = document.createTextNode(tempGang);
                        var element=document.getElementById('Gangtemp');
                        element.append(node);
                        node = document.createTextNode(timeGang);
                        element=document.getElementById('Gangdate');
                        element.append(node);
                    } else if (result.items[i].name == "DS1820-stue") {
                        tempStue=trimNumber(result.items[i].value.split(';')[1],1);
                        //timeStue=result.items[i].value.split(';')[0];
                        timeStue=result.items[i].logtime;
                        printDebug("Current temp Stue"+timeStue+" "+tempStue);
                        var node = document.createTextNode(tempStue);
                        var element=document.getElementById('Stuetemp');
                        element.append(node);
                        node = document.createTextNode(timeStue);
                        element=document.getElementById('Stuedate');
                        element.append(node);
                    }
                }
            }, // success
            error: function(error,xhr) {
                alert('Ingen kontant med IOT Cloud');
                printDebug(xhr.status);
                printDebug(xhr.responseText);
            }  // error
        });
    }
    </script>
   </head>
    <body onload="initPageV2()"> 
      <p class="swtext">Trykk på knapp for å sette termostat lav/høy</p>
      <div>
      <div class="swtext">
	 <!-- <body onload="initPage()"> 
      <p class="swtext">Trykk på knapp for å sette termostat lav/høy</p>
      <div>
      <div class="swtext"> -->
<?php
    //
    // Table for flip zone on or off
    //
    echo '<table class="termstate"><tr><th>Sone</th><th> </th></tr>';
    foreach ($rooms as $room) {
        //
        // Find state of current 
        // 
        if (array_key_exists($room,$socketsState)) {
           $selectedtemp=false;
           foreach ($groups as $group) {
               if ($group['groupname'] == $room) {
                   $selectedtemp=$group['selectedtemp'];
               break;
               }
           }
          if ($selectedtemp == 'H') {    
              echo '<tr><td>'.$room.'</td> <td> <label class="switch">';
              echo '<input id="cb'.$room.'" type="checkbox" onclick="setCBValue('."'".$room."')".'"checked>"';
              echo '<span class="slider round"></span></td></tr>';
           } else if ($selectedtemp == 'L') {
               echo '<tr><td>'.$room.'</td> <td> <label class="switch">';
               echo '<input id="cb'.$room.'" type="checkbox" onclick="setCBValue('."'".$room."')".'">"';
               echo '<span class="slider round"></span></td></tr>';
           }
        }
        
    }
    echo '</table></div><br>';
    //
    // table to set ower and upper bunds of termostat
    // only applicable for groups with sensors set
    //
    echo '<form><table class="settings-table"><tr><th class="theader">Sone </th><th class="theader">Lav</th><th class="theader">Høy</th></tr>';

    foreach ($rooms as $room) {
        //
        // Iterate throug groups to find the value of the thermostat flag
        //
        $gotThermostat='none';
        foreach ($groups as $group) {
            if ($group['groupname'] == $room) {
                $gotThermostat=$group['usetermostat'];
                $low=$group['lowtemp'];
                $high=$group['hightemp'];
            break;
            }
        } 
        if($gotThermostat == 'Y') {
            echo '<tr><td class="tright ts" size="8">'.$room.'</td>';
            echo '<td class="tright ts"><input class="tright ts noborder" type="text" id= "l'.$room.'" name="l'.$room.'" value="'.$low.'" size="8"></td>';
            echo '<td class="tright ts"><input class="tright ts noborder" type="text" id= "h'.$room.'" name="h'.$room.'" value="'.$high.'" size="8"></td></tr>';
        }

    }
    echo '</table><br><input class="bupdate" type="button" value="Oppdater termostat" onclick="setLimits()"></form><br>';
    //
    // table for gettin vales from IOT cloud
    // Only "stue2 and "gang" got temp values
    //
    echo '<table class="temp-table"><tr>';
    echo '<th class="theader">Sone </th><th class="theader">Temp</th><th class="theader">Tidspunkt</th><th class="theader">Status</th></tr>';
    foreach ($rooms as $room) {
        echo '<tr> <td class="tright ts" id="'.$room.'zone">'.$room.'</td>';
        echo      '<td class="tright ts" id="'.$room.'temp">'.$tempState[$room].'</td>';
        echo      '<td class="tright ts" id="'.$room.'date" size="20">'.$timeState[$room].'</td>';
		if (array_key_exists($room,$socketsState)) {
          echo      '<td class="tright ts" id="'.$room.'state">'.$socketsState[$room].'</td></tr>';
		} else {
		  echo      '<td class="tright ts" id="'.$room.'state">Av</td></tr>';
		}
    }
    if ($Advanced || $DEBUGFLAG>0 ) {
       echo '</table></div>';
	   echo '<br>'.$ipAdressPi1.' (one.com)<br>';
	   echo '<br>'.$ipAdressPi2.' (unoeuro)<br>';
    }
?>
   </body>
</html>