<?php
/*
*  error.php
*  Upload2USB App error
*/

?>

<?php if (isset($usb_count) && $usb_count == 0): ?>
  <link rel="stylesheet" href="/upload2usb/upload-simple.css">
  <div class="u2uform">
      <form id="insert_usb_prompt"> Insert a USB stick into your Internet-in-a-Box (IIAB) to allow students to upload their own work!</form>
  </div>

<?php else: ?>

  ERROR: Please make sure <span style="color:red; font-weight:bold;"> one and ONLY one </span>(no more, no less) removable USB stick is plugged into your Internet-in-a-Box. Please see IIAB FAQ, "<a href="https://wiki.iiab.io/go/FAQ#Can_students_upload_their_own_work?" style="font-weight:bold;">Can students upload their own work?</a>", for additional support.
  
  <br/><br/>
  <pre><?php if (isset($exception_msg)) {echo (string)$exception_msg;} ?></pre>
<?php endif; ?>




