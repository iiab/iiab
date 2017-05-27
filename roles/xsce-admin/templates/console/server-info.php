<?php
/*
*  server_info.php
*  send server and client ip to client
*/
// phpinfo();

exec("pgrep xsce-cmdsrv", $pids);
if(empty($pids))
  $cmdsrv_running = "FALSE";
else
  $cmdsrv_running = "TRUE";

header('Content-type: application/json');
echo '{"xsce_server_ip":"'.$_SERVER['SERVER_ADDR'].'","xsce_client_ip":"'.$_SERVER['REMOTE_ADDR'].'","xsce_cmdsrv_running":"'.$cmdsrv_running.'"}';
?>
