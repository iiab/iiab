<?php
/*
*  upload-file.php
*  Upload2USB App - Process Submission
*/

include("upload2usb.php");

//get folder path where file will be stored
$target_folder_path = getTargetFolderPath(1);
$target_file = $target_folder_path . "/" . basename($_FILES["uploaded_file"]["name"]);
$upload_ok = 1;
$upload_msg = "";

if(!isset($_POST["submit"]) || empty(basename($_FILES["uploaded_file"]["name"]))) {
    $upload_msg = "No file submitted.";
    $upload_ok = 0;
} elseif (file_exists($target_file)) {
  $upload_msg = "This file already exists.";
  $upload_ok = 0;
}

// Check if $upload_ok is set to 0 by an error
if ($upload_ok == 0) {
  $upload_msg = "&#x274C; Your file was not uploaded. " . $upload_msg;

// if everything is ok, try to upload file
} else {
  if (move_uploaded_file($_FILES["uploaded_file"]["tmp_name"], $target_file)) {
    $upload_msg = "&#x1F60A; &#x2705; Your file <span style=\"font-weight:bold; font-style:italic;\">". htmlspecialchars( basename( $_FILES["uploaded_file"]["name"])). "</span> was successfully uploaded!";
  } else {
    $upload_msg = "&#x274C; There was an error uploading your file. " . $upload_msg;
  }
}

$file_count = getFileCount($target_folder_path)

?>

<!DOCTYPE html>
<html>

  <head>
    <title>IIAB Upload to USB App</title>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link rel="stylesheet" href="/common/css/bootstrap4.min.css"/>
    <link rel="stylesheet" href="/common/css/fa.all.min.css"/>
    <link rel="stylesheet" href="/common/css/font-faces.css"/>
    <script src="/common/js/jquery.min.js"></script>
    <script src="/common/js/bootstrap4.min.js"></script>
  </head>
  <body class="text-center" style="background-color:#f5f5f5;">
    <div id="container" class="container">
            <div class="row">
		<div class="col-sm-6 offset-sm-3 text-center" style="padding:15px;">

                    <img class="mb-4" src="unleash-kids-swing.png" alt="" width="75">
                    <h1 class="h3 mb-3 font-weight-normal">Internet in a Box Upload to USB</h1>
                    <?php echo $upload_msg ?> <br/>
                    <?php echo $file_count ?> files have been submitted today!

		</div>
            </div>
    </div>
    
</body>
</html>

