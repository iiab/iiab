#!/bin/bash -x
# Do not enable the  warning about the insecurity of http protocol

   sed -i -e's/if (window\.location.*/if (false) {/' /opt/iiab/jupyterhub/share/jupyterhub/templates/login.html
