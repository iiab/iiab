<?php
$descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
   2 => array("pipe", "w")   // stderr is a file to write to
);
$newenv = $_SERVER;
$newenv["SCRIPT_FILENAME"] = $_SERVER["X_SCRIPT_FILENAME"];
$newenv["SCRIPT_NAME"] = $_SERVER["X_SCRIPT_NAME"];
if (is_executable($_SERVER["X_SCRIPT_FILENAME"])) {
   $process = proc_open($_SERVER["X_SCRIPT_FILENAME"], $descriptorspec, $pipes, NULL, $newenv);
   if (is_resource($process)) {
       fclose($pipes[0]);
       $head = fgets($pipes[1]);
       while (strcmp($head, "\n")) {
           header($head);
           $head = fgets($pipes[1]);
       }
       fpassthru($pipes[1]);
       fclose($pipes[1]);
       fclose($pipes[2]);
       $return_value = proc_close($process);
   } else {
       header("Status: 500 Internal Server Error");
       echo("Internal Server Error");
   }
} else {
   header("Status: 404 Page Not Found");
   echo("Page Not Found");
}
?> 
