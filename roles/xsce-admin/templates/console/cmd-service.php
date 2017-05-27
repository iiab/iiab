<?php
/*
*  xsce-cmdsrv service handler
*  Connects DEALER socket to ipc:///run/cmdsrv_sock
*  Sends command, expects response json back
*/
$time_start = microtime(true);
$request_timeout = 30000; //  REQUEST_TIMEOUT in milliseconds

$command = $_POST['command'];
//$command = "TEST";
// echo "Command: $command <BR>";
$alert_param = ',"Alert": "True"';

$read = $write = array();

// See if XSCE-CMDSRV is running

if (file_exists("/var/run/xsce-cmdsrv.pid")) {
	if (file_exists("/var/run/xsce-cmdsrv-ready")) {
    try {
      $context = new ZMQContext();
      $requester = new ZMQSocket($context, ZMQ::SOCKET_DEALER);

      //  Socket to talk to server
      $requester->connect("ipc:///run/cmdsrv_sock");
      $requester->setSockOpt(ZMQ::SOCKOPT_LINGER, 0);

      $requester->send($command);

      $poll = new ZMQPoll();
      $poll->add($requester, ZMQ::POLL_IN);
      $events = $poll->poll($read, $write, $request_timeout);
      if ($events > 0) {
        $reply = $requester->recv();
        if (strpos($reply, '"Error":') === false) {
          $reply = '{"Data": ' . $reply;
        }
      } else {
      	$reply = '{"Error": "No Response from XSCE-CMDSRV in ' . $request_timeout . ' milliseconds"' . $alert_param;
      }
    } catch (Exception $e) {
      $reply = '{"Error": "' . $e->getMessage() . '"' . $alert_param;
    }
  } else {
  	$reply = '{"Error": "XSCE-CMDSRV has started but is not ready."' . $alert_param;
  }

} else {
    $reply = '{"Error": "XSCE-CMDSRV is not running."' . $alert_param;
}

$time_end = microtime(true);
$time = $time_end - $time_start;

if (strpos($reply, '"Error":') === false) {
  $reply = $reply . ',"Resp_time": "' . $time . '"}';
}

// $time = microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"]; php 5.4 up

header('Content-type: application/json');
echo $reply;
?>
