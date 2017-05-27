XSCE Admin Console - Configure
==============================

When you installed the XSCE School Server, a great deal of software was included, but much of it was not turned on.

These configuration options allow you to turn various features on or off to suit the needs of your school.

Configuration is divided into the following sections:

Network Parameters
------------------

You will not usually need to touch these, but they are here in case you do and also for reference.

### Hostname and Domain Name

Both hostname and domain name can be changed, but you would normally only do this to fit into a larger networking environment.

**Warning:** If you change the Host Name or Domain Name, you will need to refresh the browser after clicking Install Configured Options.

The most important parameter is the **Role of the Server** in your network.  The server can play one of three roles

### Gateway

This means that the server has two connections, ethernet and/or wifi, and that it filters traffic from
client machines to the internet.

### Appliance

This means that the School Server is just another machine on the network and usually that its content can be reached by a browser with the URL http://schoolserver or http://schoolserver.lan.

### Lan Controller

This is similar to an Appliance except that the server is playing a network role for other machines on the network, such as supplying IP Addresses and Name Resolution.  An Appliance is a member of the network.  The Lan Controller is in charge of it.

### Override IP Addresses

There may be times when in order to fit into an existing network you need to change the IP Address of the adapter connected to that network. Again this is something you would seldom do.  There are four fields that must be entered:

**Please Note**: None of the values entered have any effect unless you **Check the Box** titled 'Check to use a static WAN IP Address instead of DHCP'.

**Static Wan IP Address** - Must be a valid IP Address.  The default is the current dynamic address if known, otherwise 127.0.0.1.

**Static Wan Mask** - Must be a valid Network Mask.  The default is the current maks if known, otherwise 255.255.255.0.

**Static Wan Gateway** - Must be a valid IP Address.  The default is the current gateway if known, otherwise 127.0.0.1.

**Static Wan Name Server** - Must be a valid IP Address.  The default is the current gateway address if known, otherwise 127.0.0.1.

### Internet Access for Installations

During the installation of the School Server all of the software packages were stored for future use when you might not have an Internet connection. But as long as you do have an Internet connection any future installations or updates still cause packages to download from the Internet.  If you want to use the stored packages even when you have an Internet connection you can check this box.

**Please Note:** This parameter will only be rarely changed.

### Admin Console Security

The Admin Console, this program, is password protected.  You can further protect it by requiring an encrypted connection to the School Server. This less convenient because of the questions it will cause the browser to ask, but may be necessary if you think someone might spy on traffic on the network.

Internet Caching/Filtering
--------------------------

**Please Note**: These parameters only take effect when you have selected the Gateway Role on the previous screen and have the necessary Network Adapters.

* Enable local Web Page storage for later fast Access (squid cache)

* Restrict Web Page Access to a Specific List of Sites (Permitted URLs)

* Block all HTTPS Access to Web Page

* Restrict Web Page Access according to Words in the Content (dansguardian)

When the School Server acts as a **Gateway** between school users and the internet it can provide two main types of services.  The first is that it can make the connection to the Internet more efficient by caching or storing responses on the server so that the next request does not need to go to the Internet. You will usually want this.

In addition, it can filter the sites that students are permitted to access in three ways.  The first is to only allow pages in the **Permitted URLs** list to be accessed; see below.  The second is that all sites accessed with https security can be blocked to prevent users from by-passing the previous filter.

The last filter is based not on URLs, but on **Words in the Content**.

Use your local policy to decide which of these filters to enable.

Server Portal
-------------

The School Server portal or home page is the main menu for accessing the various content modules on the server.

This is an aspect of the server that many wish to customize based on content choices, so we have included several alternative home pages.

* The default is simply called Home and has an icon look and feel with submenus.

* An earlier home page called xs-portal remains with multilingual capabilites and php scripts to detect the presence of content.

* For those who want to take customization further, both WordPress and Dokuwiki are installed and may be made the home page.

**Please Note**: Selecting WordPress or Dokuwiki will only take effect if you **Check its Box** titled 'Check to Enable'.

Services Enabled
----------------

The School Server has many individual pieces of software that incorporated into it when it is set up so that they do not have to be installed later when you might have a slow internet connection. Many of these are not turned on initially, but may be turned on or enabled by checking the box beside the name. Applications that are not used may also be turned off.

You should **note** that a number of items below require content to be useful.  Enabling them turns them on, but you must also optain content using the **Install Content** menu or from a portable hard disk.

Note some services listed below may not be installed and will not have a checkbox.

### For Students

* **Services for XO Laptops** such as Registration, Backup, and the Activity Server
* **Chat and Collaboration Server** for XO Laptops and Others

    If your school has OLPC XO laptops you should probably check these two.  Otherwise you do not normally need them.

* **Moodle** - a Courseware Manager and E-Learning Platform

    Moodle is one of the most widely used Learning Management Systems.  There is a great deal of course materials available for it, and it can be used to set up classes and curriculum.

* **Kiwix** -  serves Wikipediae and other content from sources below. You must also install content.

    If you want any Wiki content you problably want this.  Kiwix provides a server allows you to view and search a broad range of Wiki type material independent of the Internet.  This material is selected in **Install Content** - **Get Zim Files from Kiwix**

    The main reason you would not want this is if the server has very limited disk space.

* **Khan Academy Lite** -  serves Khan Academy videos and Exercises.  You must also install content.
* **Khan Academy Downloader** -  This is onlyt the downloader portion of the appplication which may be turned off if you don't plan to download videos.

    Khan Academy is a famous source of instructional videos originally on math topics, but now spanning numerous subjects.  KA Lite is an offline version of these videos and accompanying exercises.

* **Open Street Maps** -  from the original Internet in a Box, this is a world map to 13 or 16 levels of zoom depending on the tiles you install. You must also install content.

* **RACHEL** -  another collection of popular content from World Possible. You must also install content.

* **Calibre** - an E-Book Platform. You must also install content.

* **Pathagar** -  another E-Book Platform. You must also install content.

### Media Sharing and Printing

* **ELGG** -  a Social Networking Platform for Student Blogging, File Sharing, and Collaboration

* **OwnCloud** - a local server-based facility for sharing files, photos, contacts, calendars, etc.

* **SAMBA** provides Network File Sharing

    There is some overlap between these three.  **ELGG** allows blogging and other forms of social media.  Students and Teachers can use it to collaborate on projects or for journalling.  **OwnCloud** is great for sharing media. It has apps for phones and tablets that make it easy to drop photos and other materials onto the server for sharing. **SAMBA** gives you the ability to share directories on the server that can be accessed by Teachers and Students as if they were local to their laptops.

* **CUPS** provides support for **Printers** either directly attached to the server or on the network.

### For Monitoring and Administration

The options below are intended for administrators and people who may help with or support the installatiion of this School Server. It is best to consult with someone who set up the server to decide which of these to turn on.

* **SchoolTool** - a School Administration System.

* **XO Visualization** - Graphs of Student Usage Statistics.
* Title to Appear on XO Visualization Charts

* **Collect Statistics** on the use of Sugar Activities.

* **Monit** watches critical applications and restarts them if they fail.

* **Munin** collects and graphs system-level statistics.

* **VnStat** gathers and displays networking statistics.

* **AWStats** graphs statistics on web server usage.

* **PhpMyadmin** allows maintenance of mysql databases.

* **Open VPN** allows a secure connection between servers over the Internet for remote maintenance. You can access via a terminal or a web browser.

* **Team Viewer** TeamViewer provides a secure connection for Remote Support and Online Meetings. You can access the server with a graphical user interface and do file transfers.

Edit Permitted URLs
-------------------

Under **Configure** - **Internet Caching/Filtering** you can turn on Internet filtering to only permit access to URLs or web sites that are in this list. Here you can modify the list to add or remove sites.  To remove a site delete the line that has its URL. To add a site add a line with the site's URL.  The dot at the beginning of the line means to match anything up to that point, so .unleashkids.org is the same as www.unleashkids.org and download.unleashkids.org.

Actions
-------

### Update Permitted URLs List

Saves the list of permitted URLs edited above and makes them active.

### Save Configuration

Saves all configuration variables so that they will be used when the follwing button is clicked.

### Install Configured Server Options

**Warning:** This option will **Reconfigure your Server**. It runs the Ansible configuration software using all configuration variables that have been saved with the above button.

### Reset Network Configuration

**Warning:** This option will **Reconfigure your Server's Networking Setup**. It clears the current network parameters and re-applies network configuration variables that have been saved with the Save Configuration button.

**Note:** The last two Actions may not be run at the same time.  You should also refresh your browser after running either of them.
