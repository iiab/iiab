#!/bin/bash -x
# pull down repo wiki, and use to create offline docs
set -e
source /etc/iiab/iiab.env
REPONAME=iiab
REPO=https://github.com/iiab
WIKI=iiab-wiki
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
mkdir -p $WWWROOT$TARGET_URL/html

git clone $REPO/$REPONAME.wiki.git $INPUT

# To Do find more links to rewrite, especially after moving from xsce to iiab
for f in `ls /tmp/${WIKI}`; do
    FTRIMMED=${f%.md}
    if [ $FTRIMMED = "Home" ]; then FTRIMMED=index;fi
    pandoc -s /tmp/${WIKI}/$f -o $OUTPUT/$FTRIMMED.html
    # make links refer to local directory
    sed -i -r "/.*#.*/ s|$REPO/$REPONAME/wiki/(.*)(#.*)\">|./\1.html\2\">|" $OUTPUT/$FTRIMMED.html
    sed -i -r "/.*#.*/! s|$REPO/$REPONAME/wiki/(.*)\">|./\1.html\">|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|http://schoolserver.org/faq|/info/html/FAQ.html|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|http://wiki.laptop.org/go/IIAB/FAQ|/info/html/FAQ.html|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|http://wiki.laptop.org/go/XS_Community_Edition/FAQ|/info/html/FAQ.html|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|http://FAQ.IIAB.IO/info/html/FAQ|/info/html/FAQ.html|" $OUTPUT/$FTRIMMED.html
    sed -i -e "s|https://github.com/xsce/blob/release-6.2/\(.*\)\">|./\1.html\">|"  $OUTPUT/$FTRIMMED.html
done

rsync -av $OUTPUT/ $WWWROOT$TARGET_URL

# copy the faq and other things
lynx -reload -source http://wiki.laptop.org/go/XS_Community_Edition/FAQ >  $WWWROOT$TARGET_URL/html/FAQ.html
lynx -reload -source http://wiki.laptop.org/go/XS_Community_Edition/Security >  $WWWROOT$TARGET_URL/html/Security.html
lynx -reload -source http://wiki.laptop.org/go/XS_Community_Edition/local_vars.yml >  $WWWROOT$TARGET_URL/html/local_vars.yml
# fetch the recent release notes
lynx -reload -source https://github.com/XSCE/xsce/wiki/IIAB-6.2-Release-Notes>  $OUTPUT/IIAB-6.2-Release-Notes.md
lynx -reload -source https://github.com/XSCE/blob/release-6.2/Release-Notes6.0>  $OUTPUT/ReleaseNotes6.0.md
lynx -reload -source https://github.com/XSCE/blob/release-6.2/Release-Notes6.1>  $OUTPUT/ReleaseNotes6.1.md

pushd $OUTPUT
for f in `ls *Release*.md`; do
#    FTRIMMED=${f%.md}
    FTRIMMED=${f:0:-3}
    pandoc -s $f -o  $WWWROOT$TARGET_URL/$FTRIMMED.html
    # make links refer to local directory
    sed -i -e "s|$REPO/$REPONAME/wiki/\(.*\)\">|./\1.html\">)|"  $WWWROOT$TARGET_URL/$FTRIMMED.html
done
popd

#rm -rf $INPUT
#rm -rf $OUTPUT

popd

