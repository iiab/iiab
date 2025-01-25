<?php
/*
*  error.php
*  Upload2USB App error
*/

?>
ERROR: Please make sure <span style="color:red; font-weight:bold;"> one and ONLY one </span>(no more, no less) removable USB stick is plugged into your Internet-in-a-Box. Please see IIAB FAQ, <a href="https://wiki.iiab.io/go/FAQ#Can_students_upload_their_own_work%3F" style="font-style:italic;">Can students upload their own work?,</a> for additional support.

<br/><br/>

<pre><?php if (isset($exception)) {echo (string)$exception;} ?></pre>



