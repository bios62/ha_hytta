<?php
//
// 15/11-2018
// Benytter CURL mot getpropertyv2 for å hente fra siteproperties
// Støtter både GET og POST
//
// HTTP 404, siteide not set
// HTTP 401, not GET or POST
//
session_start();

include ("site.inc");


$httpMethod = $_SERVER['REQUEST_METHOD'];
$requestContentType = $_SERVER['CONTENT_TYPE'];

$conn=mysqli_connect("$host", "$username", "$password")or die("cannot connect"); 
mysqli_select_db($conn,"$db_name")or die("cannot select DB");

$tbl_name="currentIpV2"; // Table name

// Get the data based on the $httpMethod
$httpErrCode=200;

if( $httpMethod == "GET" ) {
    if(isset($_GET['siteid']) && !empty($_GET['siteid'])){
        $siteidtmp = $_GET['siteid'];
    } else {
        $srvmsg=array("msg","siteid not set (GET)");
        $httpErrCode=404;
    }
} else if( $httpMethod == "POST" && (strpos($requestContentType,"application/json") >= 0)) {
  
    $postRawData="";
    $webhook = fopen('php://input' , 'rb');
    while (!feof($webhook)) {
        $postRawData .= fread($webhook, 4096);
    }
    fclose($webhook);
  
    $postData=json_decode($postRawData,true);

    if(isset($postData["siteid"])) {
        $siteidtmp=$postData["siteid"];
    } else {
        $srvmsg=array("msg","siteid not set (POST)");
        $httpErrCode=404;
    }    
} else {
	$httpErrCode=401;
}

if ( $httpErrCode == 200)  {
    $siteid=mysqli_real_escape_string($conn,$siteidtmp);
    //echo "siteid: ".$siteid;
    // Get cURL resource
    $curl = curl_init();
    // Set some options - we are passing in a useragent too here
    // Post, not used
    /*url_setopt_array($curl, array(
        CURLOPT_HTTPHEADER => array(
                "cache-control: no-cache",
                "content-type: application/json"
            ),
        CURLOPT_RETURNTRANSFER => 1,
        CURLOPT_URL => 'http://revebaasen.no/php/getpropertyV2.php',
        CURLOPT_USERAGENT => 'mozilla',
        CURLOPT_POST => 1,
        CURLOPT_POSTFIELDS => json_encode(array('siteid' => $siteid,'propertyname' => "ip"))
    ));*/
    // Get current in use
    //
    $opturl='http://revebaasen.no/php/getpropertyV2.php?siteid='.$siteid.'&propertyname=ip';
    curl_setopt_array($curl, array(
        CURLOPT_HTTPHEADER => array(
                "cache-control: no-cache",
                "content-type: application/json"
            ),
        CURLOPT_RETURNTRANSFER => 1,
        CURLOPT_FOLLOWLOCATION=>TRUE,
        CURLOPT_MAXREDIRS=>10,
        CURLOPT_URL => $opturl,
        CURLOPT_USERAGENT => 'mozilla',
    ));
    // Send the request & save response to $resp
    $resp = curl_exec($curl);
    // Close request to clear up some resources
    curl_close($curl);
     mysqli_close($conn);
} 
header('Content-Type: application/json');
$srvmsg=array();

if($httpErrCode == 500) {  // SQL error
  http_response_code(500);
  $srvmsg['sqlerror']=$sqlresulttext;
  $srvmsg['statement']=$sel;
} else if($httpErrCode == 404) {  // Siteid not found in get request
    http_response_code(404);
} else if($httpErrCode == 401) {  // Wrong method
    http_response_code(401);
} else if($httpErrCode == 402) {  // Siteid not found in gmysql table
    http_response_code(402);
} else {
    http_response_code(200);
    $resparr=json_decode($resp,true);
    $srvmsg['siteid']=$resparr['siteid'];
    $srvmsg['currip']=$resparr['value'];
}

echo json_encode($srvmsg);

?>
