# Offline Internet Archive README

The Internet Archive offers perhaps the world’s largest online store of open content. 
The wisdom of the ages, just a few clicks away. As Wikipedia has become the world’s encyclopedia, 
the Internet Archive has become its library. 
Central to our mission is establishing “Universal Access to All Knowledge”. 
Access to our library of millions of books, journals, audio and video recordings and beyond is free to anyone.

This Ansible role installs the Internet Archive's dweb-mirror project on
Internet-in-a-Box (IIAB).  Use this to build up a dynamic offline library
arising from the materials you can explore at https://dweb.archive.org

The Offline Internet Archive server:

* Crawls Internet Archive collections to a local server,
* Serves that content locally,
* Caches content while browsing,
* Moves content between servers by sneakernet — on disks, USB sticks, and SD cards,
* Delivers (mostly) the Internet Archive UI offline in javascript in the browser,
* Is open source,
* And is being made available in other languages.

## Starting server

The server is started and restarted automatically.  It can be turned on or off
at a terminal window with `service internetarchive start` or `service internetarchive stop` 

## Browsing

Open the web page at [http://box:4244](http://box:4244) or
[http://box.lan:4244](http://box.lan:4244) (try
[http://box.local:4244](http://box.local:4244) via mDNS over a local network,
if you don't have name resolution set up to reach your Internet-in-a-Box).

There are several aspects to managing content on the Internet Archive’s Universal Library which are covered below, 
these include crawling content to your own system, or to an external drive suitable for moving to another system, 
and managing a collection of material on the archive that others can download automatically. 

Try walking through the following steps to get a tour of the system and understand more about:

* Using the interface
* Details page - viewing a single item
* Collection and Search pages - multiple items
* Accessing Internet Archive resources
* Managing Crawling
* Downloading content for a different box
* Managing collections on Internet Archive

Or you can click `Home` or the Internet Archive logo, 
if you just want to explore the Internet Archive's resources.

## Using the page

Whichever of the addresses above works it should bring you to your `local` start page.
You can get back here at any time, via the `Local` button.

If you have used the Internet Archive then the interface will be familiar, 
but there are a few differences to support offline use. 

At the top you'll see the Internet Archive's usual interface, a few of these buttons will (for now) only work 
while online, and don't appear when offline.

Below that is a row of information specific to the offline application.
    
First are health indicators. 

* If it shows "Mirror" in Red, it means we can't communicate with the mirror gateway, 
  this will only happen if the gateway goes offline part way through a process.
* Normally you'll see an indicator for GATEWAY, which is Green when the gateway can talk to the Archive, 
  and Red when you are offline.
* Then comes an indicator for this page, whether it is being crawled, and if so approximately how much has been stored. 
* If the mirror is online to the Internet Archive (GATEWAY shows Green), then next comes a "Reload" button, 
  you can click this to force it to check with the Archive for an up to date list. 
  It is most useful on collections when someone else might have added something, 
  but your gateway might be remembering an old version.
* Then there is a Settings button which brings up a page that includes status of any crawls.
* Finally there is a Home button which will bring you back to this page. 

Each tile on this page represents an item that your server will check for when it “crawls”.  
The first time you access the server this will depend on what was installed on the server, and it might be empty. 

Notice that most of the tiles should have a White, Green or Blue dot in the top right to indicate that you are crawling them. 

* A White dot means the item has been downloaded and enough of it has been downloaded to be viewed offline. 
* The Green dot indicates that we are checking this item each time we crawl and getting enough to display offline. 
* A Blue dot indicates we are crawling all the content of the item, this could be a lot of data, 
  for example a full resolution version of the video. Its rare that you’ll use this. 

This button also shows how much has been downloaded, for an item its the total size of downloaded files/pages,
for a collection its the total amount in all collection members. 

Tiles come in two types, most shows items that can be displayed - books, videos, audio etc, 
clicking on these will display the item. 

Some of the tiles will show a collection which is a group of items that someone has collected together, 
most likely there will be at least one collection relevant to your project put on the page during installation.  

It shows you how many items are in the collection and how many have been downloaded 
e.g. 400Mb in 10 of 123 items, means 10 of the 123 items in the collection are downloaded sufficient to view offline,
and a total of 400Mb is downloaded in this collection. (Which includes some files, like thumbnails, in other items).

## Details page - viewing a single item

If you click on an item that is already downloaded (Blue, Green or White dot) then it will be displayed offline, 
the behavior depends on the kind of item.

* Images are displayed and saved for offline use
* Books display in a flip book format, pages you look at will be saved for offline use. 
* Video and Audio will play immediately and you can skip around in them as normal

The crawl button at the top will indicate whether the object is being crawled and if not, whether it has been downloaded, 
in the same way tiles do, and also show you (approximately) the total downloaded for this item. 

Click on the Crawl button till it turns Green and it will download a full copy of the book, video or audio.
It waits about 30 seconds to do this, allowing time to cycle back to the desired level of crawling.
These items will also appear on your Local page.  
See the note above, usually you won’t want to leave it at yellow (all) as this will usually try
(there are some size limits) to download all the files.

There is a Reload button which will force the server to try archive.org, 
this is useful if you think the item has changed, or for debugging.

If you want to Save this item to a specific disk, for example to put it on a USB-drive then click the Save button.  
This button brings up a dialogue with a list of the available destinations. 
These should include any inserted drive with "archiveorg" as a directory at its top level. 
The content will be copied to that drive, which can then be removed and inserted into a different server.

The server checks whether these disks are present every 15 seconds, so to use a new USB disk:

* Insert the USB 
* Create a folder at its top level called `archiveorg`
* Wait about 15 seconds
* Reload the page you are on
* Hitting `Save` should now allow this USB disk to be selected. 

## Collection and Search pages - multiple items

If you click on a Collection, then we’ll display a grid of tiles for all the items that have been placed in the collection. 
White, Green and Blue indicators mean the same as on the Local page. 
If you click on the crawl button till its Green then it will check this collection each time it crawls, 
download the tiles for the first page or so, and can be configured to get some of the items as well 

## Accessing Internet Archive resources

The Internet Archive logo tile on the local page will take you to the Archive front page collection, 
content here is probably not already downloaded or crawled, 
but can be selected for crawling as for any other item.

## Managing crawling

If you click on the "Settings" button, it should bring up a page of settings to control Crawling.
This page is still under development (as of June 2019). 

On here you will see a list of crawls.
You should get useful information about status, any errors etc. 
Hitting `<<` will restart the crawl and `||` or `>` pause and resume,
but note that any file already being downloaded will continue to do so when you hit pause. 
Hitting `||` `<<` `<` will stop the current crawl, reset and retry, which is a good way to try again if,
for example, you lost connection to the server part way through.   

## Crawling

The Crawler runs automatically at startup and when you add something to the crawl, 
but it can also be configurable through the YAML file described above
or run at a command line for access to more functionality.

In a shell
```
sudo sh
```
cd into the location for your installation
```
cd /opt/iiab/internetarchive/node_modules/@internetarchive/dweb-mirror
```
Perform a standard crawl
```
./internetarchive --crawl 
```
To fetch the "foobar" item from IA
```
./internetarchive --crawl foobar 
```
To crawl top 10 items in the prelinger collection sufficiently to display and put 
them on a disk plugged into the /media/pi/xyz.
```
./internetarchive --copydirectory /media/pi/xyz/archiveorg --crawl --rows 10 --level details prelinger
```
To get a full list of possible arguments and some more examples
```
./internetarchive --help
```

### Advanced crawling

If you have access to the command line on the server, then there is a lot more you can do with the crawler.

The items selected for crawling (Green or Blue dots) are stored in a file `dweb-mirror.config.yaml` 
in the one directory of the server, e.g. on IIAB its in `/root/dweb-mirror.config.yaml`
and on your laptop its probably in `~/dweb-mirror.config.yaml`.
You can edit this file with care! 

From the command line, cd into the installation
```
cd /opt/iiab/internetarchive/node_modules/dweb-mirror
./internetarchive --crawl
```
There are lots of options possible, try `./internetarchive —help` to get guidance.

This functionality will be gradually added to the UI in future releases.
In the meantime if you have something specific you want to do feel free to post it as a new issue on 
[github](https://github.com/dweb-mirror/issues/new).

## Downloading content for a different box

You can copy one or more items that are downloaded to a new storage device (e.g. a USB drive), 
take that device to another Universal Library server, and plug it in.  
All the content will appear as if it was downloaded there. 

To put content onto a device, you can either:
* put the `copydirectory` field in the yaml file described above, 
* hit `Save` while on an item or search
* or run a crawl at the command line 

cd into your device e.g. on an IIAB it would be 
``` 
cd /media/pi/foo
```
Create a directory to use for the content, it must be called "archiveorg"
```
mkdir archiveorg 
```
cd to the installation
```
cd /opt/iiab/internetarchive/node_modules/dweb-mirror
```
Copy the current crawl to the directory
```
./internetarchive --crawl --copydirectory /media/foo/archiveorg
```
When its finished, you can unplug the USB drive and plug into any other device 

Alternatively if you want to crawl a specific collection e.g. `frenchhistory` to the drive, you would use:
```
./internetarchive --crawl --copydirectory /media/foo/archiveorg frenchhistory
```
If you already have this content on your own device, then the crawl is quick, 
and just checks the content is up to date. 

## Managing collections on Internet Archive

You can create and manage your own collections on the [Internet Archive site](https://www.archive.org).  
Other people can then crawl those collections. 

First get in touch with Mitra Ardron at `mitra@archive.org`, as processes may have changed since this is written.

You'll need to create an account for yourself at [archive.org](https://archive.org)

We'll setup a collection for you of type `texts` - dont worry, you can put any kind of media in it. 

Once you have a collection, lets say `kenyanhistory`
you can upload materials to the Archive by hitting the Upload button and following the instructions.

You can also add any existing material on the Internet Archive to this collection.  

* Find the material you are looking for
* You should see a URL like `https://archive.org/details/foobar`
* Copy the identifier which in this case would be `foobar`
* Go to `https://archive.org/services/simple-lists-admin/?identifier=kenyanhistory&list_name=items` 
replacing `kenyanhistory` with the name of your collection.
* Enter the name of the item `foobar` into the box and click `Add`. 
* It might take a few minutes to show up, you can add other items while you wait. 
* The details page for the collection should then show your new item `https://archive.org/details/kenyanhistory`

On the device, you can go to `kenyanhistory` and should see `foobar`.
Hit `Refresh` and `foobar` should show up. 
If `kenyanhistory` is marked for crawling it should update automatically

## Administration

Administration is carried out mostly through the same User Interface as browsing. 

Select `local` from any of the pages to access a display of local content. 
Administration tools are under `Settings`.

Click on the Archive logo, in the center-top, to get the Internet
Archive main interface if connected to the net. 

While viewing an item or collection, the `Crawl` button in the top bar
indicates whether the item is being crawled or not.  Clicking it will cycle
through three levels:

* No crawling
* Details - sufficient information will be crawled to display the page, for a
  collection this also means getting the thumbnails and metadata for the top
  items. 
* Full - crawls everything on the item, this can be a LOT of data, including
  full size videos etc, so use with care if bandwidth/disk is limited.

### Disk storage

The server checks for caches of content in directories called `archiveorg` in
all the likely places, in particular it looks for any inserted USB drives
on most systems, and if none are found, it uses `~/archiveorg`.

The list of places it checks, in an unmodified installation can be seen at 
`https://github.com/internetarchive/dweb-mirror/blob/master/configDefaults.yaml#L7`.

You can override this in `dweb-mirror.config.yaml` in the home directory of the
user that runs the server. (Note on IIAB this is currently in `/root/dweb-mirror.config.yaml`)
(see 'Advanced' below)

Archive's `Items` are stored in subdirectories of the first of these
directories found, but are read from any of the locations. 

If you disk space is getting full, its perfectly safe to delete any
subdirectories (except `archiveorg/.hashstore`), and the server will refetch anything else it needs 
next time you browse to the item while connected to the internet. 
Its also safe to move directories to an attached USB 
(underneath a `archiveorg` directory at the top level of the disk) 
It is also safe to move attached USB's from one device to another.

Some of this functionality for handling disks is still under active development, 
but most of it works now.

### Maintenance

If you are worried about corruption, or after for example hand-editing or
moving cached items around. 

Run everything as root
```
sudo su
```
cd into location for your installation
```
cd /opt/iiab/internetarchive/node_modules/@internetarchive/dweb-mirror
./internetarchive -m
```
This will usually take about 5-10 minutes depending on the amount of material
cached,  just to rebuild a table of checksums.

### Advanced

Most functionality of the tool is controlled by two YAML files, the second of
which you can edit if you have access to the shell. 

You can view the current configuration by going to `/info` on your server.
The default, and user configurations are displayed as the `0` and `1` item in
the `/info` call. 

In the Repo is a
[default YAML file](https://github.com/internetarchive/dweb-mirror/blob/master/configDefaults.yaml)
which is commented. It would be a bad idea to edit this, so I'm not going to
tell you where it is on your installation! But anything from this file can be
overridden by lines in `/root/dweb-mirror.config.yaml`. Make sure you
understand how yaml works before editing this file, if you break it, you can
copy a new default from
[dweb-mirror.config.yaml on the repo](https://github.com/internetarchive/dweb-mirror/blob/master/dweb-mirror.config.yaml)

Note that this file is also edited automatically when the Crawl button
described above is clicked. 

As the project develops, this file will be more and more editable via a UI. 

## More info

Dweb-Mirror lives on GitHub at:
* dweb-mirror (the server) [source](https://github.com/internetarchive/dweb-mirror),
  and [issues tracker](https://github.com/internetarchive/dweb-mirror/issues)
* dweb-archive (the UI) [source](https://github.com/internetarchive/dweb-archive),
  and [issues tracker](https://github.com/internetarchive/dweb-archive/issues)

This project is part of the Internet Archive's larger Dweb project, see also:
* [dweb-universal](https://github.com/mitra42/dweb-universal) info about others working to bring access offline.
* [dweb-transports](https://github.com/internetarchive/dweb-transports) for our transport library to IPFS, WEBTORRENT, WOLK, GUN etc
* [dweb-archivecontroller](https://github.com/internetarchive/dweb-archivecontroller) for an object oriented wrapper around our APIs
