<?php
/*
*  upload-file.php
*  Upload2USB App - Process Submission
*/

$title = "Upload to USB Results";
include("upload2usb.php");

//get folder path where file will be stored
$target_folder_path = getTargetFolderPath(1);
$uploaded_filename = basename($_FILES["uploaded_file"]["name"]);
$target_file = $target_folder_path . "/" . $uploaded_filename;
$upload_ok = 1;
$upload_msg = "";

if(!isset($_POST["submit"]) || !is_uploaded_file($_FILES['uploaded_file']['tmp_name'])) {
    $upload_msg = "No file uploaded!";
    $upload_ok = 0;
} elseif (!isFileMimeTypeAcceptable($_FILES["uploaded_file"]["tmp_name"])) {
    $upload_msg = "You cannot upload zips, executables, xml, or binary files!";
    $upload_ok = 0;
} elseif (file_exists($target_file)) {

    if (!isFileContentUnique($target_folder_path, $_FILES["uploaded_file"]["tmp_name"])) {
         $upload_msg = "This file already exists!";
	 $upload_ok = 0;
    } else {
         // rename file so name is unique
	 $new_filename = getUniqueFileName($target_folder_path, $uploaded_filename);
    	 $target_file = $target_folder_path . "/" . $new_filename;
    }
}

// Check if $upload_ok is set to 0 by an error
if ($upload_ok == 0) {
  $upload_msg = "&#x274C; Your file was not uploaded. " . $upload_msg;

// if everything is ok, try to upload file
} else {
  if (move_uploaded_file($_FILES["uploaded_file"]["tmp_name"], $target_file)) {
    $upload_msg = "&#x1F60A; &#x2705; Your file <span style=\"font-weight:bold; font-style:italic;\">". htmlspecialchars( $uploaded_filename ). "</span> was successfully uploaded!";
  } else {
    $upload_ok = 0; 
    throw new RuntimeException('There was an error uploading your file. <br/><br/>');
  }
}

$file_count = getFileCount($target_folder_path);
//$requesting_url = $_SERVER['REQUEST_URI']; 

?>

<?php include("header.php"); ?>

                    <?php echo $upload_msg ?> <br/>
                    <?php echo $file_count ?> files have been uploaded today!

<?php include ("footer.php"); ?>


