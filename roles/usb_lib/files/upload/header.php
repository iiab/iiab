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
  </head>
  <body class="text-center" style="background-color:#f5f5f5;">
    <div id="container" class="container">
            <div class="row">
		<div class="col-sm-6 offset-sm-3 text-center" style="padding:15px;">

                    <img class="mb-4" src="uk-swing.png" alt="" width="75">
                    <h1 class="h3 mb-3 font-weight-normal"><?php echo $title ?></h1>
