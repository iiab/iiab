<?php
/*
*  index.php
*  Homework Submission App Index Page
*/

include("hw.php");

//Check if folder for today exists, and get file count if it does

$file_count = getFileCount(getTargetFolderPath(0));

?>

<!DOCTYPE html>
<html>

  <head>
    <title>IIAB Homework Submission App</title>
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

                  <form action="submit-hw.php" id="hw_submission_form" method="post" enctype="multipart/form-data">
                    <img class="mb-4" src="unleash-kids-swing.png" alt="" width="75">
                    <h1 class="h3 mb-3 font-weight-normal">Internet in a Box Homework Submission</h1>

                    <label for="submit_hw" style="font-weight:bold;padding-bottom:10px;">Submit your homework here!</label>
                    <input type="file" name="hw_submission" id="hw_submission"><br/><br/>
                    <button class="btn btn-dark" name="submit" type="submit" style="width:150px;">Submit</button>
                  </form>
                  <br/>
                    <?php echo $file_count ?> homework files have been submitted today!

                </div>
            </div>
    </div>

</body>
</html>
