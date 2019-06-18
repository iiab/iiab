#! /bin/sh
### BEGIN INIT INFO
# Provides:          nginx
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: nginx init.d dash script for Ubuntu or other *nix.
# Description:       nginx init.d dash script for Ubuntu or other *nix.
### END INIT INFO
#------------------------------------------------------------------------------
# nginx - this Debian Almquist shell (dash) script, starts and stops the nginx
#         daemon for Ubuntu and other *nix releases.
#
# description:  Nginx is an HTTP(S) server, HTTP(S) reverse \
#               proxy and IMAP/POP3 proxy server.  This \
#               script will manage the initiation of the \
#               server and it's process state.
#
# processname: nginx
# config:      /usr/local/nginx/conf/nginx.conf
# pidfile:     /usr/local/nginx/logs/nginx.pid
# Provides:    nginx
#
# Author:  Jason Giedymin
#          <jason.giedymin AT gmail.com>.
#
# Version: 3.9.0 12-MAY-2015 jason.giedymin AT gmail.com
# Notes: nginx init.d dash script for Ubuntu.
# Tested with: Ubuntu 14.10, nginx-1.7.9
#
# This script's project home is:
#   http://github.com/JasonGiedymin/nginx-init-ubuntu
#
#------------------------------------------------------------------------------
#                               MIT X11 License
#------------------------------------------------------------------------------
#
# Copyright (c) 2008-2013 Jason Giedymin, http://jasongiedymin.com
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#                               Functions
#------------------------------------------------------------------------------
LSB_FUNC=/lib/lsb/init-functions

# Test that init functions exists
test -r $LSB_FUNC || {
    echo "$0: Cannot find $LSB_FUNC! Script exiting." 1>&2
    exit 5
}

. $LSB_FUNC

#------------------------------------------------------------------------------
#                               Consts
#------------------------------------------------------------------------------
# Include nginx defaults if available
if [ -f /etc/default/nginx ]; then
    . /etc/default/nginx
fi

# Minimize path
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

PS=${PS:-"nginx"}                             # process name
DESCRIPTION=${DESCRIPTION:-"Nginx Server..."} # process description
NGINXPATH=${NGINXPATH:-/usr/local/nginx}      # root path where installed
DAEMON=${DAEMON:-$NGINXPATH/sbin/nginx}       # path to daemon binary
NGINX_CONF_FILE=${NGINX_CONF_FILE:-$NGINXPATH/conf/nginx.conf} # config file path

PIDNAME=${PIDNAME:-"nginx"}                   # lets you do $PS-slave
PIDFILE=${PIDFILE:-$PIDNAME.pid}              # pid file
PIDSPATH=${PIDSPATH:-$NGINXPATH/logs}         # default pid location, you should change it
RUNAS=${RUNAS:-root}                          # user to run as

SCRIPT_OK=0           # ala error codes
SCRIPT_ERROR=1        # ala error codes
TRUE=1                # boolean
FALSE=0               # boolean

#------------------------------------------------------------------------------
#                               Simple Tests
#------------------------------------------------------------------------------

# Test if nginx is a file and executable
test -x $DAEMON || {
    echo "$0: You don't have permissions to execute nginx." 1>&2
    exit 4
}

# You can also set your conditions like so:
# set exit condition
# set -e

#------------------------------------------------------------------------------
#                               Functions
#------------------------------------------------------------------------------

setFilePerms(){
    if [ -f $PIDSPATH/$PIDFILE ]; then
        chmod 400 $PIDSPATH/$PIDFILE
    fi
}

configtest() {
    $DAEMON -t -c $NGINX_CONF_FILE
}

getPSCount() {
    return `pgrep -f $PS | wc -l`
}

isRunning() {
    if [ $1 ]; then
        pidof_daemon $1
        PID=$?

        if [ $PID -gt 0 ]; then
            return 1
        else
            return 0
        fi
    else
        pidof_daemon
        PID=$?

        if [ $PID -gt 0 ]; then
            return 1
        else
            return 0
        fi
    fi
}

#courtesy of php-fpm
wait_for_pid () {
    try=0

    while test $try -lt 35 ; do
        case "$1" in
            'created')
            if [ -f "$2" ]; then
                try=''
                break
            fi
            ;;

            'removed')
            if [ ! -f "$2" ]; then
                try=''
                break
            fi
            ;;
        esac

        try=`expr $try + 1`
        sleep 1
    done
}

status(){
    isRunning
    isAlive=$?

    if [ "${isAlive}" -eq $TRUE ]; then
        log_warning_msg "$DESCRIPTION found running with processes:  `pidof $PS`"
        rc=0
    else
        log_warning_msg "$DESCRIPTION is NOT running."
        rc=3
    fi

    return
}

removePIDFile(){
    if [ $1 ]; then
        if [ -f $1 ]; then
            rm -f $1
        fi
    else
        #Do default removal
        if [ -f $PIDSPATH/$PIDFILE ]; then
            rm -f $PIDSPATH/$PIDFILE
        fi
    fi
}

start() {
    log_daemon_msg "Starting $DESCRIPTION"

    isRunning
    isAlive=$?

    if [ "${isAlive}" -eq $TRUE ]; then
        log_end_msg $SCRIPT_ERROR
        rc=0
    else
        start-stop-daemon --start --quiet --chuid \
        $RUNAS --pidfile $PIDSPATH/$PIDFILE --exec $DAEMON \
        -- -c $NGINX_CONF_FILE
        status=$?
        setFilePerms

        if [ "${status}" -eq 0 ]; then
            log_end_msg $SCRIPT_OK
            rc=0
        else
            log_end_msg $SCRIPT_ERROR
            rc=7
        fi
    fi

    return
}

stop() {
    log_daemon_msg "Stopping $DESCRIPTION"

    isRunning
    isAlive=$?

    if [ "${isAlive}" -eq $TRUE ]; then
        start-stop-daemon --stop --quiet --pidfile $PIDSPATH/$PIDFILE

        wait_for_pid 'removed' $PIDSPATH/$PIDFILE

        if [ -n "$try" ]; then
            log_end_msg $SCRIPT_ERROR
            rc=0 # lsb states 1, but under status it is 2 (which is more prescriptive). Deferring to standard.
        else
            removePIDFile
            log_end_msg $SCRIPT_OK
            rc=0
        fi
    else
        log_end_msg $SCRIPT_ERROR
        rc=7
    fi

    return
}

reload() {
    configtest || return $?

    log_daemon_msg "Reloading (via HUP) $DESCRIPTION"

    isRunning

    if [ $? -eq $TRUE ]; then
        kill -HUP `cat $PIDSPATH/$PIDFILE`
        log_end_msg $SCRIPT_OK
        rc=0
    else
        log_end_msg $SCRIPT_ERROR
        rc=7
    fi

    return
}

quietupgrade() {
    log_daemon_msg "Peforming Quiet Upgrade $DESCRIPTION"

    isRunning
    isAlive=$?

    if [ "${isAlive}" -eq $TRUE ]; then
        kill -USR2 `cat $PIDSPATH/$PIDFILE`
        kill -WINCH `cat $PIDSPATH/$PIDFILE.oldbin`

        isRunning
        isAlive=$?

        if [ "${isAlive}" -eq $TRUE ]; then
            kill -QUIT `cat $PIDSPATH/$PIDFILE.oldbin`
            wait_for_pid 'removed' $PIDSPATH/$PIDFILE.oldbin
            removePIDFile $PIDSPATH/$PIDFILE.oldbin

            log_end_msg $SCRIPT_OK
            rc=0
        else
            log_end_msg $SCRIPT_ERROR

            log_daemon_msg "ERROR! Reverting back to original $DESCRIPTION"

            kill -HUP `cat $PIDSPATH/$PIDFILE`
            kill -TERM `cat $PIDSPATH/$PIDFILE.oldbin`
            kill -QUIT `cat $PIDSPATH/$PIDFILE.oldbin`

            wait_for_pid 'removed' $PIDSPATH/$PIDFILE.oldbin
            removePIDFile $PIDSPATH/$PIDFILE.oldbin

            log_end_msg $SCRIPT_OK
            rc=0
        fi
    else
        log_end_msg $SCRIPT_ERROR
        rc=7
    fi

    return
}

terminate() {
    log_daemon_msg "Force terminating (via KILL) $DESCRIPTION"

    PIDS=`pidof $PS` || true

    [ -e $PIDSPATH/$PIDFILE ] && PIDS2=`cat $PIDSPATH/$PIDFILE`

    for i in $PIDS; do
        if [ "$i" = "$PIDS2" ]; then
            kill $i
            wait_for_pid 'removed' $PIDSPATH/$PIDFILE
            removePIDFile
        fi
    done

    log_end_msg $SCRIPT_OK
    rc=0
}

destroy() {
    log_daemon_msg "Force terminating and may include self (via KILLALL) $DESCRIPTION"
    killall $PS -q >> /dev/null 2>&1
    log_end_msg $SCRIPT_OK
    rc=0
}

pidof_daemon() {
    PIDS=`pidof $PS` || true

    [ -e $PIDSPATH/$PIDFILE ] && PIDS2=`cat $PIDSPATH/$PIDFILE`

    for i in $PIDS; do
        if [ "$i" = "$PIDS2" ]; then
            return 1
        fi
    done

    return 0
}

action="$1"
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart|force-reload)
        stop
        # if [ $rc -ne 0 ]; then
        #     script_exit
        # fi
        sleep 1
        start
        ;;
    reload)
        $1
        ;;
    status)
        status
        ;;
    configtest)
        $1
        ;;
    quietupgrade)
        $1
        ;;
    terminate)
        $1
        ;;
    destroy)
        $1
        ;;
    *)
        FULLPATH=/etc/init.d/$PS
        echo "Usage: $FULLPATH {start|stop|restart|force-reload|reload|status|configtest|quietupgrade|terminate|destroy}"
        echo "       The 'destroy' command should only be used as a last resort."
        exit 3
        ;;
esac

exit $rc
