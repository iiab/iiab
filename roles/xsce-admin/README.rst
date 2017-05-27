=================
XSCE Admin README
=================

This role is home to a number of administrative playbooks.  Those implemented are:

Add Administrative User
-----------------------

* Add the xsce-admin user and password
* N.B. to create password hash use python -c 'import crypt; print crypt.crypt("<plaintext>", "$6$<salt>")'
* Make a sudoer
* Add /root/.ssh and dummy authorized_keys file as placeholder
* Force password for sudoers

Add Packages for Remote Access
------------------------------

* screen
* lynx

Add Command Server
------------------

* Command Server escalates privileges to root for web user

Add Admin Console and Dependencies
----------------------------------

* Gui configuration tool


XSCE-CMDSRV
===========

The purpose of xsce-cmdsrv application is to run various administrative tasks
initiated by the Admin Console with privilege escalated to the root level.

Security
--------

xsce-cmdsrv listens on an ipc socket readable and writeable only by root and
members of the xsce-admin group. It accepts commands on this channel which must
be in a list of acceptable commands and which it then translates into actual
actions to take on the server

Commands and Jobs
-----------------

Commands are received from the front end and turned into actions by xsce-cmsrv.
Some actions take little time and are executed immediately and the result returned
to the front end. Others may be long running and are tracked as jobs.  On startup
xsce-cmdsrv checks to see if there jobs that did not complete and tries to restart
them.  The frontend can query the output and status of these jobs and can cancel jobs.

Command Data Structure
----------------------

* rowid - used as cmd_id key
* cmd_msg text - text of command received from the front end
* create_datetime text - datetime of insertion

Job Data Structure
------------------

* rowid -used as job_id key
* cmd_rowid integer - foreign key to command table
* cmd_step_no integer - the number of the step in multi-step commands
* depend_on_job_id integer - the job_id of the job that must complete before this starts
* has_dependent text - Y/N does this job have a dependent job
* job_command text - the job string that will be passed to the subprocess module
* job_pid integer - pid of a running job
* job_output text - any output from the job executable
* job_status text - one of SCEDULED, STARTED, RESTARTED, SUCCEEDED, FAILED, or CANCELLED
* create_datetime text - datetime of insertion
* last_update_datetime text - datetime of last update

Storage
-------

The persistent storage for this application is essentially single user so
sqlite has been used for speed and simplicity.
