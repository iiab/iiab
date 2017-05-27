#!/bin/bash -x
# pull down repo wiki, and imbed in docs subdirectory

source /etc/xsce/xsce.env
REPONAME=xsce
REPO=https://github.com/XSCE
WIKI=xsce-wiki
TARGET_URL=/info
WWWROOT=/library/www/html
INPUT=/tmp/${WIKI}
OUTPUT=/tmp/${WIKI}.out

# this script is located in the scritps/ directory in the local repo
SCRIPTDIR=$(dirname $0)
pushd $SCRIPTDIR

rm -rf $INPUT
rm -rf $OUTPUT
mkdir -p $INPUT
mkdir -p $OUTPUT

git clone $REPO/$REPONAME.wiki.git $INPUT

# convert the markdown docs to html
which pandoc
if [ $? -ne 0 ]; then
   if [ "$OS" = "CentOS" ] || [ "$OS" = "Fedora" ]; then
      yum install -y pandoc
   else
      apt-get install -y pandoc
   fi
fi
mkdir -p $WWWROOT$TARGET_URL/html

# To Do find more links to rewrite, especially after moving from xsce to iiab
for f in `ls /tmp/${WIKI}`; do
    FTRIMMED=${f%.md}
    if [ $FTRIMMED = "Home" ]; then FTRIMMED=index;fi
    pandoc -s /tmp/${WIKI}/$f -o $OUTPUT/$FTRIMMED.html
    # make links refer to local directory
    sed -i -e "s|$REPO/$REPONAME/wiki/\(.*\)\">|./\1.html\">|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|http://schoolserver.org/faq|/info/html/FAQ|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|$REPO/$REPONAME/blob/release-.*/\(.*\)\">|./\1.html\">|"  $OUTPUT/$FTRIMMED.html
done

rsync -av $OUTPUT/ $WWWROOT$TARGET_URL

# copy the faq and other things
lynx -reload -source http://wiki.laptop.org/go/XS_Community_Edition/FAQ >  $WWWROOT$TARGET_URL/html/FAQ
lynx -reload -source http://wiki.laptop.org/go/XS_Community_Edition/Security >  $WWWROOT$TARGET_URL/html/Security
lynx -reload -source http://wiki.laptop.org/go/XS_Community_Edition/local_vars.yml >  $WWWROOT$TARGET_URL/html/local_vars.yml

# fetch the embedded help pages from the admin console
#for f in `ls ../roles/xsce-admin/files/console/help`; do
#    FTRIMMED=${f%.rst}
#    pandoc -s ../roles/xsce-admin/files/console/help/$f -o ../docs/html/offline-help/$FTRIMMED.html
#    # make links refer to local directory
#    sed -i -e "s|$REPO/$REPONAME/wiki/\(.*\)\">|./\1.html\">)|" ../docs/html/$FTRIMMED.html
#done

# fetch the recent release notes
for f in `ls ../Release*`; do
#    FTRIMMED=${f%.md}
    FTRIMMED=${f:2}
    pandoc -s $f -o  $WWWROOT$TARGET_URL$FTRIMMED.html
    # make links refer to local directory
    sed -i -e "s|$REPO/$REPONAME/wiki/\(.*\)\">|./\1.html\">)|"  $WWWROOT$TARGET_URL$FTRIMMED.html
done

rm -rf $INPUT
rm -rf $OUTPUT

popd

