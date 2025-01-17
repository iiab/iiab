<?php
/*
*  error.php
*  Upload2USB App error
*/

?>

ERROR: Please make sure <span style="color:red; font-weight:bold;"> one and ONLY one </span>(no more, no less) removable USB stick is plugged into your Internet-in-a-Box. Please see IIAB FAQs for additional support: <a href="https://wiki.iiab.io/go/FAQ#Can_teachers_display_their_own_content%3F">FAQ #4 - Can teachers display their own content?</a>, <a href="https://wiki.iiab.io/go/FAQ#What_are_the_best_places_for_community_support%3F">FAQ #49 - What are the best places for community support?.</a>

<br/><br/>

<pre><?php if (isset($exception)) {echo (string)$exception;} ?></pre>



