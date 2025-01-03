<?php
/*
*  hw.php
*  Homework Submission App Helpder Functions
*/


//return the first removable USB drive location
function getTargetUSBDriveLocation () {
         // Get the first removal USB drive using
         // lsblk --output NAME,TRAN,RM,MOUNTPOINT --pairs |grep RM=\"1\" | grep -v MOUNTPOINT=\"\" |grep -oP '[^/]MOUNTPOINT="\K[^"]*' -m 1
         // lsblk --output NAME,TRAN,RM,MOUNTPOINT --pairs |grep RM=\"1\" | grep -v MOUNTPOINT=\"\" | cut -d " " -f 4 | cut -d "=" -f 2

         $removable_usb_path = trim(str_replace('"', '', shell_exec('lsblk --output NAME,TRAN,RM,MOUNTPOINT --pairs |grep RM=\"1\" | grep -v MOUNTPOINT=\"\" | cut -d " " -f 4 | cut -d "=" -f 2')));

         if (empty($removable_usb_path)) {
                return "/library/www/html/local_content/";
         } else {

                return $removable_usb_path . "/";
         }

}

//returns folder path where homework will be stored, if create_folder_p = 1, it will create the folder if it doesn't exist
function getTargetFolderPath ($create_folder_p) {
         $parent_dir = getTargetUSBDriveLocation();


error_log("PARENTDIR: " . $parent_dir);

         $today_folder_name = "UPLOADS." . date("Y-m-d");
         $target_folder_path = $parent_dir . $today_folder_name;

         if (!file_exists($target_folder_path) && $create_folder_p) {
            mkdir($target_folder_path, 0777);

        }

        return $target_folder_path;

}

//return number of files within a specified folder
function getFileCount ($folder_path) {
        return count(glob($folder_path . "/*"));
}

//*** TODO *** check file content to see if it's unique or not
function isFileContentUnique ($file) {


}


//*** TODO **** check if file exists based on file name and return unique name if does
function getUniqueFileName ($filename) {

}


// Check file size - we are not going to check file size for now.
// elseif ($_FILES["hw_submission"]["size"] > 5000000) {
//  $upload_msg = "Your file is too large.";
//  $upload_ok = 0;
// }

?>
