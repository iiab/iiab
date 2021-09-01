#!/bin/bash -x
# Do not enable the  warning about the insecurity of http protocol

   sed -i -e's/if (window\.location.*/if (false) {/' {{ jupyterhub_venv }}/share/jupyterhub/templates/login.html
