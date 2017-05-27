XSCE Admin Console - Install Content
====================================

The options on this menu allow you to download and install content onto the School Server.  As of this release all of this content comes from the internet, but in the future there will be menu options to copy from a portable hard disk drive.

These options are aimed at people who plan to set up the server in a location where there is a relatively high bandwidth connection and then deploy it where there is little or no connectivity.

Get Zim Files from Kiwix
------------------------

### Overview

The words Zim and Kiwix are probably unfamiliar, but the content is very familiar and highly desirable, including all or some of the following for more than 100 languages:

* Wikipedia
* Wiktionary
* TED Talks
* Project Gutenberg Books
* Wikibooks
* Wikiquote
* Wikinews
* Wikivoyage
* Others

Kiwix.org supplies a server that is installed on the School Server and also hosts all of this content.

### Do this First

Click on the button labelled **Refresh Kiwix Catalog** if you have not done so before or if it has been a month or more since you last did so.  This will retrieve the latest list of content hosted at Kiwix.org.

### How it works

When you Click on this menu option you will see a list of any content already installed, any in the process of being installed, and all content available in the languages selected.

To select more languages Click on the button labelled **Select Languages**.  You will see the six languages with the most speakers in the world.  Click **More Languages** for others.  Check the language you want and then click **Show Content** or the **x** in the top right of the screen.

Next **Check the Titles** you want to download.  You will see the total space available and the amount required for your selections.  Be aware that the download process can require approximately double this amount.

When you have made your selections click **Install Selected Zims**.  Jobs will be created on the server to download, unzip, and install the selected content.  These are large files and the download can take a long time.  Visit **Display Job Status** on the **Utilities** menu to see when they have completed or any problems encountered.  It is not necessary to keep the browser open during the download.

### Don't Forget

When all of the Zim files have been downloaded and installed the Kiwix server needs to be restarted, which can be done by clicking **Restart the Kiwix Zim Server**.

Make sure that the **Kiwix** service is enabled under **Configure** - **Services Enabled**.

Download Khan Academy Videos
----------------------------

### How it works

KA Lite from the Learning Equality Foundation is installed on the School Server for offline viewing of Khan Academy videos and exercises.  It has its own options to select language and download videos.  To access this functionality simply click **Launch KA Lite** and another tab will open where you can login and manage content.

### Don't Forget

Make sure that the **Khan Academy Lite** and **Khan Academy Downloader** services are enabled under **Configure** - **Services Enabled**.

Get RACHEL
----------

RACHEL from worldpossible.org is another collection of content which includes as of the rachelusb_32EN_3.1.5 release:

* Khan Academy - Math and Science (without exercises)
* Medline Plus Medical Encyclopedia
* Hesperian Health Guides
* Khan Academy - Health & Medicine
* Infonet-Biovision
* Practical Action
* Project Gutenberg, 400 Selected Titles
* CK-12 Textbooks
* OLPC Educational Packages
* UNESCO's IICBA Electronic Library
* Math Expression
* Powertyping
* MIT Scratch
* Understanding Algebra

### How it works

The screen displays whether RACHEL is installed, enabled, and whether the content has been installed.

To download, unzip, and install the above content click **Download RACHEL Content**.  This is a single, large file and the whole process can take a long time. Visit **Display Job Status** on the **Utilities** menu to see when they have completed or any problems encountered.  It is not necessary to keep the browser open during the download.

Particular content items can be removed from the RACHEL menu (but not from the server), by moving them from the rachel/www/modules directory to rachel/www/modules.out. In the future it will be possible to do this using this menu option.

### Please Note

With the current version of RACHEL there are errors in several files that may cause this download to fail part way through the first time.  However, it will succeed on a subsequent try.  If you see that it has failed when visting the **Display Job Status** screen, please return to this screen and click **Download RACHEL Content**.  The download and unzip will resume from the point at which it failed.

### Don't Forget

Make sure that the **RACHEL** service is enabled under **Configure** - **Services Enabled**.  The content can be downloaded if it is not enabled, but will only be visible to students after RACHEL has been enabled.

Remove Downloaded Files
-----------------------

By installing Zim files or RACHEL you are downloading large files from the internet.  These are not removed in case there is a problem and the installed needs to be rerun.

After you are sure that everything has been installed successfully you can remove some or all of these files to free up space on the disk.

Here is how to verify that an item has been installed:

* Look at the installation page and ensure that the item is marked as installed.
* Look at the School Server menu to see it the item is accessible and brings up content.

Actions
-------

**Restart the Kiwix Zim Server** and **Refresh Kiwix Catalog** are covered above.

**Refresh Zims Installed** recalculates the amount of space used on the disk.