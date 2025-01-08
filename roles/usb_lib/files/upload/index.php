<?php
/*
*  index.php
*  Upload2USB App Index Page
*/

include("upload2usb.php");

//Check if folder for today exists, and get file count if it does

$file_count = getFileCount(getTargetFolderPath(0));

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

                  <form action="upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
                    <img class="mb-4" src="uk-swing.png" alt="" width="75">
                    <h1 class="h3 mb-3 font-weight-normal">Internet in a Box Upload to USB</h1>

                    <label for="upload2usb" style="font-weight:bold;padding-bottom:10px;">Upload your file here!</label><br/>
                    <input type="file" name="uploaded_file" id="uploaded_file"><br/><br/>
                    <button class="btn btn-dark" name="submit" type="submit" style="width:150px;">Submit</button>
                  </form>
                  <br/>
                    <?php echo $file_count ?> files have been uploaded today!

                </div>
            </div>
    </div>

</body>
</html>
