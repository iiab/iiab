<?php
/*
*  upload2usb.php
*  Upload2USB App Helper Functions
*/

set_exception_handler(function (Throwable $exception) {
    error_log('UPLOAD2USB ERROR: ' . (string)$exception);
    $requesting_url = $_SERVER['REQUEST_URI']; 

    // If user is on the main app page (i.e., /upload2usb/), show the error on the page, otherwise fail silently
    if (strcmp($requesting_url,"/upload2usb/") == 0 || strcmp($requesting_url,"/upload2usb/index.php") == 0) {
        include ("error.php");
    }
});

//return the first removable USB drive location
function getTargetUSBDriveLocation () {

         // Get the count of storage mounted at /media, and error if there is <>1 otherwise return upload path

         $rmv_usb_path_count = shell_exec('lsblk --output NAME,TRAN,RM,MOUNTPOINT --pairs | cut -d " " -f 4 | grep "^MOUNTPOINT=\"/media" | wc -l');

         if ($rmv_usb_path_count == 0) {
               throw new RuntimeException('0 USB sticks found. <br/><br/>');
         } elseif ($rmv_usb_path_count > 1) {
               throw new RuntimeException('More than 1 USB sticks installed. <br/><br/>');
         }

         $rmv_usb_path = trim(str_replace('"', '', shell_exec('lsblk --output NAME,TRAN,RM,MOUNTPOINT --pairs | cut -d " " -f 4 | grep "^MOUNTPOINT=\"/media" | cut -d "=" -f 2')));

         if (empty($rmv_usb_path)) {
               throw new RuntimeException('Not able to find USB stick. <br/><br/>');
         } else {
               return $rmv_usb_path . "/";
         }
}

//returns folder path where file will be stored, if create_folder_p = 1, it will create the folder if it doesn't exist
function getTargetFolderPath ($create_folder_p) {
         $parent_dir = getTargetUSBDriveLocation();

         $today_folder_name = "UPLOADS." . date("Y-m-d");
         $target_folder_path = $parent_dir . $today_folder_name;

         if (!file_exists($target_folder_path) && $create_folder_p) {
               mkdir($target_folder_path, 0777) or throw new RuntimeException("Not able to create upload directory. <br/>Make sure 'usb_lib_writable_sticks' is set to 'True'. <br/><br/>");
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
