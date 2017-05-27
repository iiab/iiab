# Release Notes for XSCE 6.0

## What is it?

XSCE is the digital backbone for your education revolution. Put simply, School Server is an open-education project inspired by
One Laptop Per Child to provide breakthrough digital learning tools to the world’s poorest children.

### A Rose by any other Name

Internally and in the source code we refer to this software as XSCE, the Community Edition of the XS server originally from
OLPC. Students and teachers often know it as Internet in a Box, a collection of educational materials and applications found on the internet,
but available on the server even without an internet connection.  We also refer to it as a School Server since it is aimed at
schools and other places where people learn and performs the function of a server.

## What's new in XSCE Release 6.0?

This release extends the tools available to educators in three ways:

* It makes available free and open source content that is available in many languages
* It provides new avenues for students to create, and share their work
* It contains number of advances to permit easy configuration, tailoring of content, and monitoring of student work.

### Newly Available Open Source Educational Content


* KA Lite brings the online features of **Khan Academy** to the **offline** schoolserver based classroom. There are videos, exercises, tests, and student tracking in a number of languages, all selectable via a Graphical User Interface. https://learningequality.org/ka-lite/
* Searchable **offline** access to **Wikipedia** and other content such as Wiktionaries and TED Talks in a variety of subjects and many languages, provided by the **Kiwix server** technology. http://www.kiwix.org/wiki/Main_Page
* RACHEL (a currated selection of offline materials) http://worldpossible.org/rachel/
* Bring your **own content** by inserting a **USB thumbdrive** with content into the server having it immediately viewable by students.

### Encourage Students to Write, Foster the Creative Process

* Elgg provides the tools for generating social networks http://learn.elgg.org/en/2.0/intro/features.html
* ownCloud provides client based tools for storing and retrieving materials stored on the XSCE local cloud.
* DokuWiki (EXPERIMENTAL) provides a means for students to publish their work. https://www.dokuwiki.org/features
* Wordpress (EXPERIMENTAL -- enable in "local_vars") gives students experience editing/sharing using a tool that is becoming an industry standard.

### New Tools for Administering the XSCE schoolserver

* A new Graphical User Interface (Admin Console) to enable services, select and download content, get information
* AWstats is a flexible tool for summarizing the web traffic on and through the server in graphical and detailed ways. http://www.awstats.org/

## How do I get it?

There are three main methods of installing this software:

* Use ansible and the git repository - this is the fall back when you need to customize or you have a platform for which we have not created an image.
* Use an image you download - for some commonly used platforms we create image files that you can download, put on a usb stick or sd card and boot in your new hardware.
* Create and use your own image - this will appeal to you if you want an image to use in multiple machines and are able to use the tools we provide to create it.

In each case you need hardware that has been assembled, but with nothing installed on it.

Detailed instructions on each of these methods is at https://github.com/XSCE/xsce/wiki/XSCE-Installation.
