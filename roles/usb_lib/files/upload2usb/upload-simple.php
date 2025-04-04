<?php
/*
*  upload-simple.php
*  Upload2USB App simple upload page
*/

include("upload2usb.php");

//Check if folder for today exists, and get file count if it does
$file_count = getFileCount(getTargetFolderPath(0));

//TODO: Check if upload_msg exists and display result if it does - this is not yet working quite right.
$url_components = parse_url($_SERVER['REQUEST_URI']);
//error_log ("URL: ". var_dump($url_components));
$upload_msg = "";
if (array_key_exists("query", $url_components)) {
  parse_str($url_components['query'], $query);
  $upload_ok = $query['upload_ok'];
//  error_log ("UPLOAD_OK: " . $upload_ok);
  if ($upload_ok == 1) {
    $upload_msg = "Your file was successfully uploaded!";
  } else {
    $upload_msg = "There was an error uploading your file.";
  }
  $upload_msg = "<span class='upload_msg'>".$upload_msg."</span>";
}
?>

<script>
     function uploadFile() {
       document.getElementById("uploaded_file").click();
     };
</script>

<style>
    div.container {
      text-align:center;
      width:260px;
      max-width:350px;
      float:right;
      color: #fff;
    }
    @media (max-width:768px) {
      div.container {
        float:none !important;
	margin:auto;
      }
    }
    form {
      background-color: #333;
      border-radius:.3rem;
      padding:.5rem;
    }
    button {
      background-color: #ddd;
      border: none;
      border-radius:.3rem;
      color: #333;
      padding: .25rem .25rem;
      text-align: center;
      text-decoration: none;
      display: inline-block;
      font-size:.85rem;
      font-weight:bold;
      width:225px;
    }
    button:hover {
      color: #666;
    }
    span {
      display:block;
      margin-top:5px;
      text-align:center;
      font-size:.8rem;

    }

/* TODO: FIX FADING
    .upload_msg{
      transition: 5s opacity, 5s visibility;
      opacity: 1;
    }

    .upload_msg.fade{
       opacity: 0;
       visibility: hidden;
    }
*/
    
</style>

<div class="container">
    <form action="/upload2usb/upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
        <input type="file" name="uploaded_file" id="uploaded_file" onChange="this.form.submit();" style="display:none;">
	<button name="upload_btn" type="button" onClick="uploadFile();">Upload to USB</button>
        <span><?php echo $file_count ?> files uploaded today!</span>
	<?php echo $upload_msg ?>
    </form>
</div>





