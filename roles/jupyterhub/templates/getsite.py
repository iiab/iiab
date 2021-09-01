#!{{jupyterhub_venv }}/bin/python3

import site

for path in iter(site.getsitepackages()):
    if path.find('site') != -1:
        print(path)
