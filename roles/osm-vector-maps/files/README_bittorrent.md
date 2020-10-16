## Initialize and Manage a Local BitTorrent Cache of Map files
#### Overview
Files uploaded to Archive.org can be downloaded via the bittorrent protocol. This protocol allows many computers to distribute files in a peer-to-peer manner, by dividing a file into many "chunks". A bittorrent client gets its instructions from a torrent file. Early versions of bittorrent clients needed to contact a bittorrent "seeder" (or server), to get a list of peers who might be able to supply any of these chunks. The main advantage of using bittorrent, for IIAB, is that the downloading can proceed at a much faster rate when there are a number of "seeders" across the internet who are providing chunks simultaneously. 
#### Setting up a BitTorrent Cache using IIAB-get-torrent.py
The IIAB-get-torrent.py program is a python script which controls the bitTorrent client (named transmissioon-daemon). This python program provides a connection between the map_catalog.json which specifies the required maps, and the transmission-daemon which actually does the downloading, and peer-to-peer file sharing. It has a number of options which are outlined below:
#### Use help to remember the meaning o the options
```
./iiab-bittorrent-get.py -h
usage: iiab-bittorrent-get.py [-h] [-a] [-c] [-g GET] [-i IDX] [-l] [-p] [-t]
                              [-u UPLD]

Download OSM Bittorrent files.

optional arguments:
  -h, --help            show this help message and exit
  -a, --all             Start downloading all Archive.org maps.
  -c, --catalog         List Map Catalog Index numbers and torrent info.
  -g GET, --get GET     Download Map via Catalog key (MapID).
  -i IDX, --idx IDX     Download Map via Index number from -c option above.
  -l, --link            Make bittorrent files available to maps.
  -p, --progress        Show progress of current bitTorrent downloads.
  -t, --torrents        List status of local torrents.
  -u UPLD, --upld UPLD  Max upload speed in KB. Set to 0 to disable uploading.

```
#### Use -c --catalog option to see which of the IIAB Maps are already in your BitTorrent Cache
```
root@box:/opt/iiab/iiab/roles/osm-vector-maps/files# ./iiab-get-torrent.py -c
Index:  5  20.4 MiB 100%   2.7 GiB  seeding Region: World to Zoom Level 10
Index: 10  20.6 GiB 100%  23.2 GiB  seeding Region: North America
Index: 20   2.9 GiB 100%   5.5 GiB  seeding Region: Central America
Index: 25  13.8 GiB 100%  16.4 GiB  seeding Region: Spanish Speakers
Index: 30   9.8 GiB 100%  12.4 GiB  seeding Region: South America
Index: 40  26.4 GiB 100%  29.0 GiB  seeding Region: Europe
Index: 50  13.0 GiB 100%  15.7 GiB  seeding Region: Africa
Index: 60   7.5 GiB 100%  10.1 GiB  seeding Region: Middle East
Index: 70  16.6 GiB 100%  19.2 GiB  seeding Region: North Asia
Index: 80  10.7 GiB 100%  13.3 GiB  seeding Region: South Asia
Index: 90   5.5 GiB 100%   8.1 GiB  seeding Region: Oceania
Index: 95   0.0       0%  78.6 GiB   absent Region: World
root@box:/opt/iiab/iiab/roles/osm-vector-maps/files# 
```
#### Use -t --torrent option to examine which BitTorrent files exist in your cache -- some may not be Map files
```
root@box:/opt/iiab/iiab/roles/osm-vector-maps/files# ./iiab-get-torrent.py -t
100%   7.5 GiB osm_middle_east_z11-z14_2019.mbtiles
100%  13.0 GiB osm_africa_z11-z14_2019.mbtiles
100% 433.0 MiB 2020-02-13-raspbian-buster-lite.zip
100%   1.8 GiB ubuntu-18.04-desktop-amd64.iso
100% 291.0 MiB debian-9.6.0-amd64-netinst.iso
100%   2.5 GiB 2020-02-13-raspbian-buster-full.zip
100%   2.9 GiB osm_central_america_z11-z14_2019.mbtiles
100%   2.2 GiB ka-lite-0.17-resized-videos-hindi
100%  26.4 GiB osm_europe_z11-z14_2019.mbtiles
100%  10.7 GiB osm_south_asia_z11-z14_2019.mbtiles
100%  20.6 GiB osm_north_america_z11-z14_2019.mbtiles
100%   5.5 GiB osm_oceania_z11-z14_2019.mbtiles
100% 906.0 MiB CentOS-7-x86_64-Minimal-1804
100%  10.0 GiB ka-lite-0.17-resized-videos-french
100%   9.8 GiB osm_south_america_z11-z14_2019.mbtiles
100%  20.4 MiB osm_san_jose_z11-z14_2019.mbtiles
100%  13.8 GiB osm_spanish_speaking_regions_z11-z14_2019.mbtiles
100%  16.6 GiB osm_north_asia_z11-z14_2019.mbtiles
100%  43.6 GiB ka-lite-0.17-resized-videos-english
root@box:/opt/iiab/iiab/roles/osm-vector-maps/files# 
```
#### Use -u --UPLD to set the upload speed, when you are willing to share your MAP data with others. Setting the -u --UPLD value to 0 (zero) disables uploading. The IIAB default, without changeing local_ars.yml, is to disable uploading.
```
iiab-bittorrent-get.py -u 1000

Upload speed limit: 1000 KB. Limit enabled:True
```
