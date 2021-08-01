## JupyterHub programming environment with student Notebooks

#### Secondary schools may want to consider JupyterHub to integrate coding with dynamic interactive graphing — A New Way to Think About Programming — allowing students to integrate science experiment results and program output within their own blog-like "Jupyter Notebooks."

* Jupyter Notebooks are widely used in the scientific community:
  * Intitutional FAQ: https://jupyterhub.readthedocs.io/en/stable/getting-started/institutional-faq.html
  * Getting Started: https://jupyterhub.readthedocs.io/en/stable/getting-started/
* Students create their own accounts on first use — e.g. at http://box.lan/jupyterhub — just as if they're logging in regularly (the login screen doesn't make that clear, but the teacher does not need to be involved!)
  * A student can then sign in with their username and password, to gain access to their files (Jupyter Notebooks).
  * The teacher should modify and protect JupyterHub's overall ``Admin`` password, just in case: http://FAQ.IIAB.IO#What_are_the_default_passwords.3F
* Individual student folders are created in ``/var/lib/private/`` on the Internet-in-a-Box (IIAB) server:
  * A student will only be able to see their own work — they do not have privileges outside of their own folder.
  * Students may upload Jupyter Notebooks to the IIAB server, and download the current state of their work via a normal browser.
