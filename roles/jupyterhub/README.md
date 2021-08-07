## JupyterHub programming environment with student Notebooks

#### Secondary schools may want to consider JupyterHub to integrate coding with dynamic interactive graphing — A New Way to Think About Programming — allowing students to integrate science experiment results and program output within their own blog-like "Jupyter Notebooks."

* Jupyter Notebooks are widely used in the scientific community:
  * [Intitutional FAQ](https://jupyterhub.readthedocs.io/en/stable/getting-started/institutional-faq.html)
  * [Getting Started](https://jupyterhub.readthedocs.io/en/stable/getting-started/)
* Students create their own accounts on first use — e.g. at http://box.lan/jupyterhub — just as if they're logging in regularly (unfortunately the login screen doesn't make that clear, but the teacher _does not_ need to be involved!)
  * A student can then sign in with their username and password, to gain access to their files (Jupyter Notebooks).
  * The teacher should set and protect JupyterHub's overall ``Admin`` password, just in case.  As with student accounts, the login screen doesn't make that clear — so just log in with username `Admin` using any password that you want to become permanent.
* Individual student folders are created in ``/var/lib/private/`` on the Internet-in-a-Box (IIAB) server:
  * A student will only be able to see their own work — they do not have privileges outside of their own folder.
  * Students may upload Jupyter Notebooks to the IIAB server, and download the current state of their work via a normal browser.

### Settings

Linux administrators please see `/opt/iiab/jupyterhub/etc/jupyterhub/jupyterhub_config.py` which originates from https://github.com/iiab/iiab/blob/master/roles/jupyterhub/templates/jupyterhub_config.py

Note that `/opt/iiab/jupyterhub` is a Python 3 virtual environment, that can be activated with the usual formula:

```
source /opt/iiab/jupyterhub/bin/activate
```

### Known Issues

* 2021-08-07: The page that allows you to reset/change your own password is not accessible.  Likewise Admin users cannot reset/change the password of any _individual_ user at this time.  <sub><sub>[#2918](https://github.com/iiab/iiab/pull/2918)</sub></sub>
  * If necessary, a Linux administrator can delete the `/passwords.dbm.db` file at the very top of your Linux filesystem, allowing all JupyterHub users to (re)create new passwords.  This does work, but is very heavy-handed.  <sub><sub>[PR #2892](https://github.com/iiab/iiab/pull/2892#issuecomment-890551682)</sub></sub>
* 2021-08-07: Teachers (i.e. Admin users) cannot currently access the very helpful "administrator's page" discussed at [JupyterHub FAQ >> "How do I manage users?"](https://jupyterhub.readthedocs.io/en/stable/getting-started/institutional-faq.html#how-do-i-manage-users) and [roles/jupyterhub/templates/jupyterhub_config.py#L1049-L1054 >> "Admin users have extra privileges"](https://github.com/iiab/iiab/blob/d0e8e048347bf46c02a2cdb0da9c5cd0c489fe40/roles/jupyterhub/templates/jupyterhub_config.py#L1049-L1054).  <sub><sub>[#2919](https://github.com/iiab/iiab/pull/2919)</sub></sub>
