<?php
/*
*  upload-simple.php
*  Upload2USB App simple upload page
*/

include("upload2usb.php");

//Check if folder for today exists, and get file count if it does
$file_count = getFileCount(getTargetFolderPath(0));

//TODO: Check if upload_msg exists and display result if it does - this is not yet working quite right. 
$upload_msg = isset($_GET['upload_msg']) ? "<br/><span>" . $_GET['upload_msg'] . "</span>": "" ;

?>

<script>
     function uploadFile() {
       document.getElementById("uploaded_file").click();
     };
</script>

<style>
    
    div.container {
      text-align:center;
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
    input {
      margin-right:-3rem;
      font-size:.75rem;
    }
    button, input[type="file"]::file-selector-button {
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
</style>

<div class="container">
    <form action="/upload2usb/upload-file.php" id="upload2usb_form" method="post" enctype="multipart/form-data">
        <input type="file" name="uploaded_file" id="uploaded_file" onChange="this.form.submit();" style="display:none;">
	<button name="upload_btn" type="button" onClick="uploadFile();">Upload</button>
        <span><?php echo $file_count ?> files uploaded today!</span>
	<?php echo $upload_msg ?>
    </form>
</div>





