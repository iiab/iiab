<?php
/*
*  upload-simple.php
*  Upload2USB App simple upload page
*/

include("upload2usb.php");

//Check if folder for today exists, and get file count if it does
$file_count = getFileCount(getTargetFolderPath(0));

?>

    <style>
    
    div.container {
      text-align:center;
      max-width:350px;
      float:right;
    }
    @media (max-width:768px) {
      div.container {
        float:none !important;
	margin:auto;
      }
    }
    form {
      background-color: #ddd;
      border-radius:.6rem;
      padding:.5rem;
    }
    input {
      margin-right:-3rem;
      font-size:.75rem;
    }
    button {
      background-color: #555;
      border: none;
      border-radius:.4rem;
      color: white;
      padding: .25rem .25rem;
      text-align: center;
      text-decoration: none;
      display: inline-block;
      font-size:.9rem;
      font-weight:bold;
    }
    button:hover {
      color: #ddd;
    }
    span {
      display:block;
      margin-top:5px;
      text-align:center;
      font-size:.75rem;

    }
    </style>
    <div class="container"> 
    <form action="/upload2usb/upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
        <input type="file" name="uploaded_file" id="uploaded_file">
        <button class="btn btn-dark" name="submit" type="submit" style="width:80px;">Upload</button><br/>
        <span><?php echo $file_count ?> files uploaded today!</span>
    </form>
    </div>





