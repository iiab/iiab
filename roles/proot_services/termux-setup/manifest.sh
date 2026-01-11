# termux-setup manifest
# Order matters: later modules can rely on functions/vars defined earlier.

MODULES=(
  "00_lib_common.sh"
  "10_mod_logging.sh"
  "20_mod_termux_base.sh"
  "30_mod_debian.sh"
  "40_mod_termux_api.sh"
  "50_mod_adb.sh"
  "60_mod_ppk_checks.sh"
  "99_main.sh"
)
