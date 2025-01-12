<?php
/*
*  error.php
*  Upload2USB App error
*/

?>

AN ERROR occurred! Please make sure <span style="color:red; font-weight:bold"> one and ONLY one </span>(no more, no less) removable USB stick is plugged into your Internet-in-a-Box. <!-- Also make sure the <span style="color:red; font-weight:bold;">usb_lib_umask0000_for_kolibri</span> parameter in your IIAB configuration file is set to True. --> Reach out to TK for help if you have any questions or continue having trouble with the setup. 
<br/><br/>

Share the below error message  with IIAB developers at TK for debugging:
<pre><?php if (isset($exception)) {echo (string)$exception;} ?></pre>



