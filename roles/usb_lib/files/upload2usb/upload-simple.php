<?php
/*
*  upload-simple.php
*  Upload2USB App simple upload page
*/

include("upload2usb.php");

//Check if folder for today exists, and get file count if it does
$file_count = getFileCount(getTargetFolderPath(0));

//Check if upload_msg exists and display result if it does
$url_components = parse_url($_SERVER['REQUEST_URI']);
//error_log("URL COMPONENTS: ". $url_components);
$upload_msg = "";
if (array_key_exists("query", $url_components)) {
  parse_str($url_components['query'], $query);
  $upload_ok = $query['upload_ok'];
  $upload_msg = $query['upload_msg'];
// error_log("MESSAGE: " . $upload_msg); 
}
?>

<link rel="stylesheet" href="/upload2usb/upload-simple.css">

<script>
     function uploadFile() {
       document.getElementById("uploaded_file").click();
     };
</script>

<div class="u2uform">
    <form action="/upload2usb/upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
        <input type="file" name="uploaded_file" id="uploaded_file" onChange="this.form.submit();" style="display:none;">
	<button name="upload_btn" type="button" onClick="uploadFile();">Upload to USB</button>
        <span><?php echo $file_count ?> files uploaded today!</span>
    </form>
</div>
<?php if ($upload_msg != ''): ?>
  <div class="overlay fade-out">
    <div class="overlay-inner">
       <br/>
       <a href="/usb/"><img class="mb-4" src="/upload2usb/uk-swing.png" alt="" width="75"></a> 
       <p><span><?php echo $upload_msg ?></span></p>
       <p><span><?php echo $file_count ?> files uploaded today!</span></p>
    </div>
  </div>
<?php endif; ?>






