# Wuzapi Role

This role installs and configures [Wuzapi](https://github.com/asternic/wuzapi), a Go-based WhatsApp API gateway, and integrates it with RapidPro.

## Requirements

*   Debian/Ubuntu-based system
*   Go (Golang) compiler (handled by the role)

## Role Variables

*   `wuzapi_install`: Set to `True` to install Wuzapi. Default is `True`.
*   `wuzapi_enabled`: Set to `True` to enable and start the Wuzapi service. Default is `True`.
*   `wuzapi_port`: The port Wuzapi listens on. Default is `8095`.

### Security Requirements (MANDATORY)

This role does **NOT** provide a default password for the admin token. You **MUST** define `wuzapi_admintoken` in your local configuration (e.g., `/etc/iiab/local_vars.yml`) or the service will fail to start/authenticate.

**Example `/etc/iiab/local_vars.yml`:**
```yaml
wuzapi_admintoken: "your_secure_admin_token"
```

## Services

This role configures and manages the following systemd service:

*   `wuzapi`: The Wuzapi API server.

## Usage

To install and enable Wuzapi, add the following to your `/etc/iiab/local_vars.yml`:

```yaml
wuzapi_install: True
wuzapi_enabled: True
# MANDATORY SECRET
wuzapi_admintoken: "your_secure_admin_token"
```

Then run the IIAB installer or roles script:
`./runrole wuzapi`
