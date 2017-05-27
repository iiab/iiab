# Release Notes for Release 6.1
**What's New?**

* Calibre -- A tool for managing a library of eBooks, modifyiing their file formats, adding search terms, and making them availabe online.
* Wordpress -- A content management system which gives students experience with editing wiki pages, blogs, menuing systems, and which is widely used.
* Dokuwiki -- An alternate wiki system, similar to wordpress, but less popular, which makes transferring wiki materials easy from one school server to another.
* Sugarizer -- Makes some of the sugar activities available to browser clients on laptops, and smart phones/tablets.
* CUPS -- Common Unix Printing System provides the ability to connect to and share network or USB connected printers.

**What's Upgraded?**

* Moodle is now upgraded to version 3.1, the most recent (long term support) version that will be supported until May 2019.
* Elgg -- A social networking application is upgraded to 2.1.
* Owncloud -- Permits sharing of all kinds of content between clients of a local server that is not internet connected (version 9).

**Do all these new Services Slow my Server down?**

A service that is installed on your hard disk, but not enabled in the administrative console, will have no impact on computer speed (will not use cpu cycles, or occupy scarce memory resources).  The XSCE default is to install everything, and only enable the few things which are essential for a server to operate.

If you want to enable a service, you must browse to http://schoolserver.lan/admin, and click on configure, services enabled, and the appropriate checkbox. In addition, many services require additional content to be downloaded, which can also be accomplished by selecting the "Install Content" header button.

**How Do I Install 6.1?**

The install instructions have not changed much since release-6.0. Please refer to https://github.com/XSCE/xsce/wiki/XSCE-Installation for the overall process -- Noting the following:

* On FC22, add "yum" to the installs prior to running the ansible playbook i.e.
```
    yum install -y git yum ansible1.9
    cd /opt
    mkdir /opt/schoolserver
    cd schoolserver
    git clone https://github.com/XSCE/xsce --branch release-6.1 --depth 1
    cd xsce
    ./install-console
```

