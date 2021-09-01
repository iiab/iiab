#!/bin/bash -x
# add await to asyncio change password function

cat {{ jupyterhub_venv }}/lib/python3.7/site-packages/firstuseauthenticator/firstuseauthenticator.py |grep 'await self.render'
if [ $? -ne 0 ];then
   echo Updating file
   sed -i -e's/self.render/await self.render/' {{ jupyterhub_venv }}/lib/python3.7/site-packages/firstuseauthenticator/firstuseauthenticator.py 
else
   echo Patch already applied. Skipping. . .
fi
   
