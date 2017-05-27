XSCE Admin Console - Utilities
==============================
The options on this menu serve to monitor and diagnose problems on the School Server and to maintain some core data.

### Change Password

Use this menu option to change the XSCE Admin Password.

The password should be at least 8 characters in length and include a mix of Upper Case, Lower Case, Numbers, and Symbols.  The server will also impose restrictions based the use of simple patterns like 123 and some words.

Please note that there is no way to recover this password without logging directly into the server and changing it as root.

### Display Job Status

Actions that will require more than a few seconds to complete are handled as long-running Jobs. In fact, some tasks create multiple jobs.  The progress and success or failure of these jobs may be monitored by visiting this menu option.  Click **Refresh Status** to update the display.

Jobs that are no longer desired may be cancelled and doing so will cancel any jobs that were created as part of the same task.  To cancel a job check the box beside it and click **Cancel Checked Jobs**
### Display Commands Log

Shows the commands sent from the browser application to the command server, any errors generated, and the response time if succeeded.

### Admin Tools

Use these tools to administer, monitor, and evaluate server usage.

### Display Ansible Facts

All software on the server has been installed using a product called ansible.  This option will tell you more than you probably wanted to know about its variables.

### Display XSCE.INI File

The xsce.ini file is where the School Server stores information about what is installed and enabled.  You can view it here.

### Display System Memory

Just what it says.

### Display System Storage

Just what it says, the amount of storage, allocated and unallocated in internal and external drives and cards.

### Perform Internet Speed Test

There are two tests that can be performed.  One downloads a 10M file and the other downloads 100M and does a smaller upload. Even the 10M can take a long time on a **slow internet connection** to the point that it never returns a result to the console.

**WARNING:** On mobile connections you should be careful not to consume excessive bandwidth as this **could lead to additional costs** from your network supplier.

