#!/bin/bash
patch -p1 {{ lokole_venv }}/lib/python{{ python_ver }}/site-packages/opwen_email_client/webapp/forms/register.py -i /tmp/register.patch
patch -p1 {{ lokole_venv }}/lib/python{{ python_ver }}/site-packages/opwen_email_client/webapp/actions.py -i /tmp/action.patch
