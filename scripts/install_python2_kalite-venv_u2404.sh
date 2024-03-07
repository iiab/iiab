#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

cat << EOF > /etc/apt/sources.list.d/python2.list
deb [trusted=yes] http://archive.ubuntu.com/ubuntu jammy main universe
deb [trusted=yes] http://archive.ubuntu.com/ubuntu jammy-updates main universe
EOF

apt update

apt -y --allow-downgrades install python3.11=3.11.0~rc1-1~22.04 python3.11-minimal=3.11.0~rc1-1~22.04 libpython3.11-stdlib=3.11.0~rc1-1~22.04 libpython3.11-minimal=3.11.0~rc1-1~22.04
apt-mark hold python3.11 python3.11-minimal libpython3.11-stdlib libpython3.11-minimal

apt -y --allow-downgrades install python3-platformdirs=2.5.1-1
apt-mark hold python3-platformdirs

apt -y install python2 python2-pip-whl python2-setuptools-whl

apt -y --allow-downgrades install python3-pip-whl=22.0.2+dfsg-1
apt-mark hold python3-pip-whl

apt -y --no-install-recommends install python3-pip=22.0.2+dfsg-1
apt-mark hold python3-pip

apt -y --allow-downgrades install python3-virtualenv=20.13.0+ds-2
apt-mark hold python3-virtualenv

apt -y --allow-downgrades install virtualenv=20.13.0+ds-2
apt-mark hold virtualenv

virtualenv --always-copy --pip 20.3.4 --setuptools 44.1.1 --no-wheel -p python2.7 /usr/local/kalite/venv

cd /usr/local/kalite/venv
source bin/activate
bin/pip install ka-lite-static --no-python-version-warning --no-cache-dir
deactivate

#apt -y remove `apt list *python2* | grep installed | awk -F / '{ print $1 }'`
apt-mark unhold $(apt-mark showhold) || true

rm /etc/apt/sources.list.d/python2.list

apt -y remove libmpdec3 python3-pip python3-wheel

apt update
apt -y upgrade    # Why 'apt upgrade' here?

# python3-venv is needed for other venv's like roles/jupyterhub, e.g. #3716.
# So we restore python3-venv originally installed by scripts/ansible -- this
# is nec b/c python3-pip-whl downgrade to 22.0.2 (line ~19 above) removes it:
apt -y install python3-venv
