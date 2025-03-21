<?php
/*
*  index.php
*  Upload2USB App Index Page
*/

$title = "Upload to USB";
include("header.php");

//Check if folder for today exists, and get file count if it does
$file_count = getFileCount(getTargetFolderPath(0));

?>

<?php include ("footer.php"); ?>