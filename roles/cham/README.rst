==========
CHAM README
==========

'Cham' is a small live video streaming platform for the Internet in a Box project. The project's name draws its inspiration from the rich cultural dance and musical traditions of the Tibetan plateau. 'Cham' is a dance form from this region.

Using It
--------

  * Keep a note of the `{{ nginx_port }}` variable's value (default:8081). This is going to be our streaming server's webroot. 
  * Turn `cham_install` and `cham_enabled` to `true` in vars.
  * Run the playbook.
  * You should see a simple webpage with a video container on `http://box.lan:8081`

  **To stream:**
  * You'll need a client side streaming application. I will share settings for OBS (Open Broadcaster Studio). 
  * Open OBS. Go to `Settings > Stream`
  * Select `Service` as `Custom`
  * Server: `rtmp://box.lan/hls`
  * Stream key: `stream`
  * Use authentication: No
  * When you click `Start Streaming` OBS should connect to the nginx rtmp/hls endpoint and you will see your streamed video in the video container on the demo page. 

Attribution
-----------

This 'cham' playbook is a contribution of the `EKA foundation <https://github.com/eka-foundaiton>`.
