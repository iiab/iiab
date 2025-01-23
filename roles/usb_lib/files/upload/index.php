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

                  <form action="upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
                    <label for="upload2usb" style="font-weight:bold;padding-bottom:10px;">Upload your file here!</label><br/>
                    <input type="file" name="uploaded_file" id="uploaded_file"><br/><br/>
                    <button class="btn btn-dark" name="submit" type="submit" style="width:150px;">Upload</button>
                  </form>
                  <br/>
                  <?php echo $file_count ?> files have been uploaded today!


<?php include ("footer.php"); ?>