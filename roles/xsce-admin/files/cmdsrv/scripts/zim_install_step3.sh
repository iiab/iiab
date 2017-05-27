#!/bin/bash

WORKINGDIR=/library/working/zims/$1
SRCDIR=$WORKINGDIR/data
DESTDIR=/library/zims

ZIMIDXPATH=`find $SRCDIR/index/ -name *.idx`
ZIMIDXNAME=`basename $ZIMIDXPATH`
ZIMIDX=/index/$ZIMIDXNAME


EXITCODE=0
rc=0

# ZIM File(s)

for zimpath in $SRCDIR/content/*.zim*
do
    zimfile=$(basename $zimpath)
    if [[ -f $DESTDIR/content/$zimfile ]]; then
        echo "Removing existing $DESTDIR/content/$zimfile."
        rm $DESTDIR/content/$zimfile
    fi
    echo "Moving $zimpath"
    mv $zimpath $DESTDIR/content/$zimfile; rc1=$?
    rc=$((rc + rc1))

done

if  [[ $rc > 0 ]]; then
    EXITCODE=1
fi

# ZIM IDX Directory

if [[ -d $DESTDIR$ZIMIDX ]]; then
    echo "$DESTDIR$ZIMIDX already exists - nothing to do"
    if [[ -d $SRCDIR$ZIMIDX ]]; then
        echo "Removing $SRCDIR$ZIMIDX"
        rm -Rf $SRCDIR$ZIMIDX
    fi
else
    if [[ -d $SRCDIR$ZIMIDX ]]; then
        echo "Moving $SRCDIR$ZIMIDX "
        mv $SRCDIR$ZIMIDX $DESTDIR$ZIMIDX; rc1=$?
    else
        echo "Can not find $SRCDIR$ZIMIDX"
        echo "Unable to move it"
        rc2=1
    fi
fi

if  [[ $rc1 > 0 || $rc2 > 0 ]]; then
    EXITCODE=1
fi

if  [[ $EXITCODE > 0 ]]; then
    exit 1
fi

echo "Removing $WORKINGDIR"
rm -Rf $WORKINGDIR

echo "Re-indexing Kiwix Library"
/usr/bin/xsce-make-kiwix-lib

exit 0
