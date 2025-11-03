# RapidPro Ansible Role for IIAB (WIP)

This Ansible role installs and configures RapidPro within an IIAB (Internet-in-a-Box) environment.

## Features

- Automates the installation of RapidPro and its dependencies (PostgreSQL, Valkey/Redis, Python, Node.js).
- Configures RapidPro for production use with Gunicorn and Nginx.
- Installs and configures Mailroom and Courier Go services.
- Provides flexible control over installation, service status, and "appliance mode" via Ansible variables.

## Requirements

This role depends on the following IIAB roles:

- `nginx`
- `postgresql`

These roles are typically installed as part of the standard IIAB setup.

## Role Variables

## Usage

1.  **Enable the role:** Add the following to `/etc/iiab/local_vars.yml`:

    ```yaml
    rapidpro_install: true
    ```

2.  **(Optional) Enable Appliance Mode:** To make RapidPro the default application, add the following to `/etc/iiab/local_vars.yml`:

    ```yaml
    rapidpro_appliance_mode: true
    ```

3.  **(Optional) Disable Services:** To install RapidPro but keep the services disabled, add the following to `/etc/iiab/local_vars.yml`:

    ```yaml
    rapidpro_enabled: false
    ```

4.  **Run the playbook:** Execute the main IIAB playbook (e.g., `iiab-install`) or run the `rapidpro` role individually:

    ```bash
    ./runrole rapidpro
    ```
