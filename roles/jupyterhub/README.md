## JupyterHub programming environment with student Notebooks

#### High Schools may want to consider JupyterHub to integrate coding with dynamic interactive graphing — A New Way to Think About Programming — allowing students to integrate science experiment results and program output within their notebook/document/blog.

* Jupyter Notebooks are widely used in the scientific community:
  * Intitutional FAQ: https://jupyterhub.readthedocs.io/en/stable/getting-started/institutional-faq.html
  * Getting Started: https://jupyterhub.readthedocs.io/en/stable/getting-started/
* This IIAB package (Ansible role) permits individual users to start using their own Notebook on the IIAB server (http://box.lan/jupyterhub) without needing an individual server account:
  * Once a user signs in with a username and password, these credentials are stored, and are used thereafter to gain access to the user's files.
  * If necessary, use Admin password: http://FAQ.IIAB.IO#What_are_the_default_passwords.3F
* Individual folders are created for all student work in the path `/var/lib/protected/` &mdash; individual students will only be able to see their own work in that directory:
  * Students will not have any privileges outside of their own folder.
  * They may upload Jupyter Notebooks from a local machine, and download the current state of their work via a normal browser download.
