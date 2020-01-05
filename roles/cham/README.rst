==========
CHAM README
==========

'Cham' is a small live video streaming platform for the Internet in a Box project. The project's name draws its inspiration from the rich cultural dance and musical traditions of the Tibetan plateau. 'Cham' is a dance form from this region.

Using It
--------

* Turn `cham_install` and `cham_enabled` to `true` in vars.
* Run the playbook.
* You should see a simple webpage with a video container on `http://box.lan/stream`
* Videos that are streamed are automatically archived in different quality levels. If you want to make them available on a public location, set `public_recordings` to `true`.
* If you are also installing the azuracast role to have online radio facility, cham offers the capability to automatically stream to a radio channel incase a live stream is taking place. The following variables are pertinent (and they need to be appropriately set in local_vars):
  * `cham_stream_to_icecast: False`
  * `cham_icecast_user: iiab-admin`
  * `cham_icecast_password: g0adm1n`
  * `cham_icecast_mount: live`
  * `cham_icecast_port: {{ (azuracast_port_range_prefix * 1000) + 5 }}`
  * `cham_icecast_bitrate: 64k`
* Of the above, `cham_icecast_user`, `cham_icecast_password` are the credentials for the **Streamer/DJ Account** setting of the radio channel. `cham_icecast_mount` and `cham_icecast_port` values need to be the same as they are in the radio channel settings, that is accessible through the Administration Console in azuracast.
 

**To stream:**
  
* You'll need a client side streaming application. I will share settings for OBS (Open Broadcaster Studio). 
* Open OBS. Go to `Settings > Stream`
* Select `Service` as `Custom`
* Server: `rtmp://box.lan/src`
* Stream key: `stream`
* Use authentication: No
* When you click `Start Streaming` OBS should connect to the nginx rtmp/hls endpoint and you will see your streamed video in the video container on the demo page. 

**Additionally, you can stream an audio only version of the stream to azuracast, if it is present on your IIAB. To do that:**

* Set `cham_stream_to_icecast: True` in your `/etc/iiab/local_vars.yml`.
* The default streaming settings (These are present in `/opt/iiab/iiab/vars/default_vars.yml`): 
  * Icecast username: iiab-admin
  * Icecast password: g0adm1n
  * Streaming port: 10005
  * Default bitrate: 64k
  * Default mount point: live
* Make sure that autodj in AzuraCast is properly setup with the above settings.

Attribution
-----------

This 'cham' playbook is a contribution of the `EKA foundation <https://github.com/eka-foundation>`.
