If you are installing or configuring IIAB Maps, **you should ignore this directory**.

But we'll explain in case you're curious:

`catalog.json` is a catalog of the latest available data. Unlike just about everything else in this repository, this file is not used directly by the IIAB Maps installation process. Instead, it is made to requested by IIAB Maps _from Github_ during installation and map upgrades. This way, as soon as a map data update is made available, we can update this file on Github and it can be installed without upgrading all of IIAB Maps.
