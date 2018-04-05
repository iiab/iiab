#!/bin/bash -e

# Installs or upgrades to the best possible Ansible release, so iiab-install
# can proceed.  Ensure you're online before running this script!

GOOD_VER="2.4.4"      # Ansible version to pip install onto OLPC XO laptops.
                      # On other OS's we install/upgrade/pin to the latest Ansible 2.4.x
                      # (Whereas for the upcoming IIAB 6.6, we'll likely
                      # recommend the very latest Ansible 2.5.x or higher)
CURR_VER="undefined"
# FOUND="false"       # NOT USED AS OF 2017-12-12
# FAMILY="undefined"  # NOT USED AS OF 2017-12-12
# below are unused for future use
# URL="NA"

export DEBIAN_FRONTEND=noninteractive

# if ! which ansible-playbook ; then
if [ ! `command -v ansible-playbook` ]; then
    echo "Installing --- Please Wait"
    if [ -f /etc/centos-release ]; then
        yum -y install ca-certificates nss epel-release
        yum -y install git bzip2 file findutils gzip hg svn sudo tar which unzip xz zip libselinux-python
        yum -y install python-pip python-setuptools python-wheel patch
        yum -y install http://releases.ansible.com/ansible/rpm/release/epel-7-x86_64/ansible-2.4.4.0-1.el7.ans.noarch.rpm
        # FOUND="true"
        # FAMILY="redhat"
#    elif [ -f /etc/fedora-release ]; then
#        CURR_VER=`grep VERSION_ID /etc/*elease | cut -d= -f2`
#        URL=https://github.com/jvonau/iiab/blob/ansible/vars/fedora-$CURR_VER.yml
#        dnf -y install ansible git bzip2 file findutils gzip hg svn sudo tar which unzip xz zip libselinux-python
#        dnf -y install python-pip python-setuptools python-wheel patch
#        FOUND="true"
#        FAMILY="redhat"
    elif [ -f /etc/olpc-release ]; then
        yum -y install ca-certificates nss
        yum -y install git bzip2 file findutils gzip hg svn sudo tar which unzip xz zip libselinux-python
        yum -y install python-pip python-setuptools python-wheel patch
        pip install --upgrade pip setuptools wheel #EOL just do it
        pip install ansible==$GOOD_VER --disable-pip-version-check
        # FOUND="true"
        # FAMILY="olpc"
    elif [ -f /etc/debian_version ] || (grep -qi raspbian /etc/*elease) ; then
        if ( ! grep -qi ansible /etc/apt/sources.list) && [ ! -f /etc/apt/sources.list.d/ansible ]; then
            apt -y install dirmngr python-pip python-setuptools python-wheel patch
            #echo "deb http://ppa.launchpad.net/ansible/ansible/ubuntu xenial main" \
            #     >> /etc/apt/sources.list.d/ansible.list
            echo "deb http://ppa.launchpad.net/ansible/ansible-2.4/ubuntu xenial main" \
                 >> /etc/apt/sources.list.d/ansible.list
            apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
        fi
        # FOUND="true"
        # FAMILY="debian"
        # Parens are optional, but greatly clarify :)
    elif (grep -qi ubuntu /etc/lsb-release) || (grep -qi ubuntu /etc/os-release); then
        apt -y install python-pip python-setuptools python-wheel patch
        #apt-add-repository -y ppa:ansible/ansible
        apt-add-repository -y ppa:ansible/ansible-2.4
        # FOUND="true"
        # FAMILY="debian"
    # fi
    # if [ ! $FOUND = "true" ]; then
    else
        echo "WARN: Could not detect distro or distro unsupported"
        exit 1
    fi
else
    #CURR_VER=`ansible --version | head -n 1 | cut -f 2 -d " "`
    CURR_VER=`ansible --version | head -1 | awk '{print $2}'`  # to match iiab-install
    echo "Current ansible version installed is $CURR_VER"
    if [ -f /etc/centos-release ] || [ -f /etc/fedora-release ]; then
        echo "Please use your system's package manager to update ansible"
        exit 0
    elif [ -f /etc/olpc-release ]; then
        echo "Please use pip package manager to update ansible"
        exit 0
    #fi
    #if [[ `grep -qi ansible /etc/apt/sources.list` ]] || [ -f /etc/apt/sources.list.d/ansible*.list ]; then
    elif (grep -qi ansible /etc/apt/sources.list) || (ls /etc/apt/sources.list.d/ansible*.list >/dev/null 2>&1) ; then
        #echo "Ansible repo(s) found within /etc/apt/sources.list*"
        echo -e '\nANSIBLE REPO(S) FOUND WITHIN /etc/apt/sources.list AND/OR /etc/apt/sources.list.d/ansible*.list -- YOU LIKELY WANT LINE "deb http://ppa.launchpad.net/ansible/ansible-2.4/ubuntu xenial main" -- AND REMOVE ALL SIMILAR LINES, IF YOU WANT TO LOCK IN/PIN TO ANSIBLE 2.4.x\n'
    else
        echo "Upstream ansible source repo not found, please uninstall ansible and re-run this script"
        exit 1
    fi
fi

if [ ! -f /etc/centos-release ] && [ ! -f /etc/fedora-release ] && [ ! -f /etc/olpc-release ]; then
    # Align IIAB with Ansible community's latest official release
    echo "Using apt to check for updates, then install/upgrade ansible"
    apt update
    apt -y install ansible=2.4*

    # TEMPORARILY USE ANSIBLE 2.4.4 (REMOVE IT WITH "pip uninstall ansible")
    #pip install ansible==2.4.4

    # TEMPORARILY USE ANSIBLE 2.4.2 DUE TO 2.4.3 MEMORY BUG. DETAILS @ https://github.com/iiab/iiab/issues/669
    #echo "Install http://download.iiab.io/packages/ansible_2.4.2.0-1ppa~xenial_all.deb"
    #cd /tmp
    #wget http://download.iiab.io/packages/ansible_2.4.2.0-1ppa~xenial_all.deb
    #apt -y --allow-downgrades install ./ansible_2.4.2.0-1ppa~xenial_all.deb
fi

# needed?
mkdir -p /etc/ansible/
echo -e '[local]\nlocalhost\n' > /etc/ansible/hosts
