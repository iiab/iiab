#!/bin/bash -x
# add await to asyncio change password function

SITE_PACKAGES=$({{ jupyterhub_venv }}/bin/getsite.py)
cat $SITE_PACKAGES/firstuseauthenticator/firstuseauthenticator.py |grep 'await self.render'
if [ $? -ne 0 ];then
   echo Updating to \"await self.render\"
   sed -i -e's/self.render/await self.render/' $SITE_PACKAGES/firstuseauthenticator/firstuseauthenticator.py 
else
   echo Await patch already applied. Skipping. . .
fi
cat $SITE_PACKAGES/firstuseauthenticator/firstuseauthenticator.py |grep data['data'].lower()'
if [ $? -ne 0 ];then
	echo Updating to data['username'].lower()
	sed -i -e's/data['username']/data['username'].lower()/' $SITE_PACKAGES/firstuseauthenticator/firstuseauthenticator.py
else
	echo username.lower() patch already applied. Skipping. . .
fi
   
