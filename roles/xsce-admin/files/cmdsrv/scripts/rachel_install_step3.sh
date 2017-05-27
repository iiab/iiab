#!/bin/bash

VERSION=$1
WORKINGDIR=/library/working/rachel/$VERSION
DESTDIR=/library/rachel

if [[ -d "$DESTDIR/www" ]]; then
  echo "Rachel content already there."
  if [[ -d "$WORKINGDIR" ]]; then
    rm -Rf $WORKINGDIR
  fi
  exit 2
fi

RACHELWORKING=$WORKINGDIR/rachelusb_32EN_3.1.4/RACHEL/bin
echo "Moving www directory"
mv $RACHELWORKING/www $DESTDIR/

mkdir -p $DESTDIR/www/modules.out

echo "Moving bin directory"
mv $RACHELWORKING/bin $DESTDIR/

echo "Removing $WORKINGDIR"
rm -Rf $WORKINGDIR

echo $VERSION > $DESTDIR/version
exit 0
