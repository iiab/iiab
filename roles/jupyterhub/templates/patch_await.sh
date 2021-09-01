#!/bin/bash -x
# add await to asyncio change password function

SITE_PACKAGES=$({{ jupyterhub_venv }}/bin/getsite.py)
cat $SITE_PACKAGES/firstuseauthenticator/firstuseauthenticator.py |grep 'await self.render'
if [ $? -ne 0 ];then
   echo Updating file
   sed -i -e's/self.render/await self.render/' $SITE_PACKAGES/firstuseauthenticator/firstuseauthenticator.py 
else
   echo Patch already applied. Skipping. . .
fi
   
