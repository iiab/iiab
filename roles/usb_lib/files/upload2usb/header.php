<?php
/*
*  header.php
*  Upload2USB App Header for all User Facing Pages
*/

include("upload2usb.php");

?>

<!DOCTYPE html>
<html>

<head>
    <title><?php echo $title ?></title>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link rel="stylesheet" href="/common/css/bootstrap4.min.css"/>
    <link rel="stylesheet" href="/common/css/fa.all.min.css"/>
    <link rel="stylesheet" href="/common/css/font-faces.css"/>
    <script src="/common/js/jquery.min.js"></script>
    <script src="/common/js/bootstrap4.min.js"></script>
    <style>
        /* Add custom styles to ensure the form fits on one line */
        #upload2usb_form {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        #upload2usb_form label {
            margin-bottom: 0;
        }
        #upload2usb_form input[type="file"] {
            flex: 1;
        }
        #upload2usb_form button {
            flex-shrink: 0;
        }
    </style>
</head>
<body class="text-center" style="background-color:#f5f5f5;">
    <div id="container" class="container">
        <div class="row">
            <div class="col-sm-6 offset-sm-3 text-center" style="padding:15px;">
                <a href="/usb/"><img class="mb-4" src="uk-swing.png" alt="" width="75"></a>
                <h1 class="h3 mb-3 font-weight-normal"><?php echo $title ?></h1>

                <!-- Add the form here -->
                <form action="upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
                    <label for="upload2usb" style="font-weight:bold;padding-bottom:10px;">Upload your file here!</label>
                    <input type="file" name="uploaded_file" id="uploaded_file">
                    <button class="btn btn-dark" name="submit" type="submit" style="width:150px;">Upload</button>
                </form>
                <br/>
                <?php echo $file_count ?> files have been uploaded today!
