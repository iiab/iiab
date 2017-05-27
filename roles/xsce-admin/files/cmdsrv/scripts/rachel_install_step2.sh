#!/bin/bash

VERSION=$1
SOURCEDIR=/library/downloads/rachel/$VERSION.zip
WORKINGDIR=/library/working/rachel/$VERSION

if [[ "$VERSION" == "rachelusb_32EN_3.1.5" ]]; then
  echo "Unzipping Version $VERSION."

  /usr/bin/unzip -quo $SOURCEDIR rachelusb_32EN_3.1.4/RACHEL/bin/bin/* rachelusb_32EN_3.1.4/RACHEL/bin/www/* -d $WORKINGDIR
  rc=$?

  case $rc in

  0)
    echo "RACHEL Unzip Successful."
    EXITCODE=0
    ;;
  1)
    echo "RACHEL Unzip Completed with Warnings."
    EXITCODE=0
    ;;
  11)
    echo "RACHEL Unzip Completed with Warnings that some files had already been extracted."
    EXITCODE=0
    ;;
  *)
    echo "RACHEL Unzip Failed."
    EXITCODE=1
    ;;
  esac

else
  echo "Unsupported Version $VERSION."
  EXITCODE=1
fi

exit $EXITCODE
