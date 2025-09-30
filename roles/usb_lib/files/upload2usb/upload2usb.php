<?php
/*
*  upload2usb.php
*  Upload2USB App Helper Functions
*/

set_exception_handler(function (Throwable $exception) {
    error_log('UPLOAD2USB ERROR: ' . (string)$exception);

    $exception_details = json_decode($exception->getMessage(), true);
    $usb_count = $exception_details['usb_count'];
    $exception_msg = $exception_details['exception_msg'];
    
    // Always include error.php for upload2usb directory requests
    include ("error.php");
});

// If there is one USB drive and it is not double mounted, return the path to it, otherwise act on the exception
function getTargetUSBDriveLocation () {

         // Enumerate /media/ mountpoints and count them
         $rmv_usb_paths = shell_exec('lsblk -no MOUNTPOINTS | grep "^/media/"');
         $rmv_usb_paths_count = substr_count($rmv_usb_paths, "\n"); 

         if ($rmv_usb_paths_count == 0) {
             $exception_data = [
               'usb_count' => 0,
               'exception_msg' => '0 USB drives found. <br/><br/>'
             ];
             throw new RuntimeException(json_encode($exception_data));
         } elseif ($rmv_usb_paths_count > 1) {
             $exception_data = [
               'usb_count' => $rmv_usb_paths_count,
               'exception_msg' => 'There is more than 1 USB drive inserted or the USB drive is double mounted. <br/><br/>'
             ];
             throw new RuntimeException(json_encode($exception_data));
         } else {
             // At this point, we know there is only 1 USB drive inserted and it is not double mounted; return the path to it
             return trim($rmv_usb_paths) . "/"; 
         }
}

//returns folder path where file will be stored, if create_folder_p = 1, it will create the folder if it doesn't exist
function getTargetFolderPath ($create_folder_p) {
         $parent_dir = getTargetUSBDriveLocation();

         $today_folder_name = "UPLOADS." . date("Y-m-d");
         $target_folder_path = $parent_dir . $today_folder_name;

         if (!file_exists($target_folder_path) && $create_folder_p) {

             $exception_data = [
               'usb_count' => -1, 
               'exception_msg' => "Not able to create upload directory. <br/>Make sure 'usb_lib_writable_sticks' is set to 'True'. <br/><br/>"
             ];
	 
             mkdir($target_folder_path, 0777) or throw new RuntimeException(json_encode($exception_data));
         }
         return $target_folder_path;
}

//return number of files within a specified folder
function getFileCount ($folder_path) {
         return count(glob($folder_path . "/*"));
}

//check if file mimetype is acceptable for upload
function isFileMimeTypeAcceptable ($file) {
         $mimetype = strtolower(mime_content_type($file));
         $invalid_mimetypes_str = array ("compress", "image/svg+xml", "octet", "text/xml", "xhtml+xml");
         foreach ($invalid_mimetypes_str as $invalid_mt_str) {
               if (str_contains($mimetype, $invalid_mt_str)) {
                     error_log('UPLOAD2USB ERROR - MIMETYPE: ' . $mimetype);
                     return false;
               }
         }
         return true;
}

//check file content to see if it's unique or not
function isFileContentUnique ($target_folder_path, $file) {
         $file_to_upload_md5 = md5_file($file);
         $usb_dir = array_diff(scandir($target_folder_path), array('..', '.'));
         foreach ($usb_dir as $dir_file) {
                 $dir_file = $target_folder_path . "/" . $dir_file;

                 if (!is_dir($dir_file)) {
                       $dir_file_md5 = md5_file($dir_file);
                       if ($file_to_upload_md5 == $dir_file_md5) {
                             return false;
                       }
                 }
         }
         return true;
}

//return unique filename
function getUniqueFileName ($target_folder_path, $filename) {
         $new_filename = $filename;
         $counter = 1;
         while (file_exists($target_folder_path . "/" . $new_filename)) {
               $counter++;
               $new_filename = pathinfo($filename,8) . '-'. $counter . "." . pathinfo($filename,4);
         }
         return $new_filename;
}

// Check file size - we are not going to check file size for now.
// elseif ($_FILES["uploaded_file"]["size"] > 5000000) {
//  $upload_msg = "Your file is too large.";
//  $upload_ok = 0;
// }


?>
