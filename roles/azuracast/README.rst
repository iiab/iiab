================
AzuraCast README
================

Install `AzuraCast <https://azuracast.com/>`_ with your `Internet-in-a-Box (IIAB) <https://internet-in-a-box.org/>`_ if you want a simple, self-hosted "web radio station" with a modern web UI/UX.  You and your community can then schedule newscasts, podcasts, music, and even do live streaming of audio content (video streaming might also be possible in future!)

As soon as you install AzuraCast with IIAB, it can stream MP3 files (and similar files) using `LiquidSoap <https://docs.azuracast.com/en/developers/liquidsoap>`_ to help you schedule or randomize playback of MP3 songs (and similar).

Please see AzuraCast's `screenshots <https://www.google.com/search?q=azuracast+screenshot&tbm=isch>`_ and `docs <./README.rst#azuracast-docs>`_.  Community implementation examples:

* https://twitter.com/internet_in_box/status/1564986581664014342
* https://youtu.be/XfiFiOi46mk

Optionally, live-streaming can also be made to work, e.g. if you install `Mixxx or BUTT <https://docs.azuracast.com/en/user-guide/streaming-software>`_ on your own.  (If so, you have many options to configure streaming with `Icecast <https://icecast.org/>`_, `Shoutcast <https://www.shoutcast.com/>`_, etc.)

Requirements
------------

AzuraCast recommends `2-to-4 GB RAM minimum <https://docs.azuracast.com/en/getting-started/requirements#system-requirements>`_.

As of 2022-08-31, AzuraCast should run on Ubuntu 22.04 and **64-bit** Raspberry Pi OS: `#1772 <https://github.com/iiab/iiab/issues/1772>`_, `AzuraCast/AzuraCast#332 <https://github.com/AzuraCast/AzuraCast/issues/332>`_, `PR #2946 <https://github.com/iiab/iiab/pull/2946>`_

Other Linux distributions may also work, at your own risk, especially if Docker runs smoothly.

NOTE: AzuraCast was designed to be installed *just once* on a fresh OS.  So ``./runrole --reinstall azuracast`` is not supported in general.  However, if you accidentally damage your AzuraCast software, IIAB has posted `technical tips <./tasks/install.yml>`_ *(use at your own risk!)* in case of emergency.

Using It
--------

* Do a normal IIAB install (https://download.iiab.io), making sure to set both variables ``azuracast_install`` and ``azuracast_enabled`` to ``True`` when IIAB's installer prompts you to edit `/etc/iiab/local_vars.yml <http://FAQ.IIAB.IO#What_is_local_vars.yml_and_how_do_I_customize_it%3F>`_
* When the IIAB software install completes, it will ask you to reboot, and AzuraCast's console will then be available at http://box.lan:12080
* That console site will prompt you to complete AzuraCast's initial setup: user accounts, managing stations, radio streams, etc.
* Finally, check out some `how-to videos <https://www.youtube.com/watch?v=b1Rxlu5P804>`_ to learn to manage your own radio station!

NOTE: When creating a station using AzuraCast's console, its default streaming ports for ``station`` and ``autodj`` need to be in the `port range 10000-10499 <https://github.com/iiab/iiab/wiki/IIAB-Networking#list-of-ports--services>`_ (ports 12080 and 12443 may also be required!)

AzuraCast Docs
--------------

- https://docs.azuracast.com
- https://docs.azuracast.com/en/getting-started/installation/post-installation-steps
- https://docs.azuracast.com/en/getting-started/settings
- https://docs.azuracast.com/en/getting-started/updates (can *DAMAGE* AzuraCast as of 2022-09-28)
- https://docs.azuracast.com/en/user-guide/streaming-software
- https://docs.azuracast.com/en/user-guide/troubleshooting
- https://docs.azuracast.com/en/user-guide/logs
- https://docs.azuracast.com/en/administration/docker
