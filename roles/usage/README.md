### Usage Statistics Describing WiFi Clients on IIAB Servers
Overview:

The *hostapd* program runs on the IIAB server, and manages all of the WiFi client connections. This **Usage** application records the identity and  byte counts for each connected device once every 2 minutes. It places this information into a sqlite3 databae (/opt/iiab/clientlinfo.sqlite). The information in the database is summarized by a graphical output page at http://box.lan/admin/usage (requires the *Admin Console* username and password).
