#!/usr/bin/env bash
# Dump the hardware facts the tuning advisor matches on.
# Run on the handheld in Desktop Mode: bash capture_device.sh > device.txt
# Attach device.txt to a device registry PR. It holds no serial numbers:
# product_serial, board_serial and product_uuid are skipped on purpose.
set -u

section() { printf '\n## %s\n' "$1"; }

section "dmi"
for f in sys_vendor product_name product_version product_family product_sku board_name board_vendor board_version bios_version; do
  path="/sys/class/dmi/id/$f"
  if [ -r "$path" ]; then
    printf '%s=%s\n' "$f" "$(tr -d '\n' < "$path")"
  else
    printf '%s=<unreadable>\n' "$f"
  fi
done

section "cpu"
grep -m1 'model name' /proc/cpuinfo | sed 's/^model name[[:space:]]*:[[:space:]]*/model_name=/'
printf 'threads=%s\n' "$(grep -c '^processor' /proc/cpuinfo)"

section "memory"
grep -m1 MemTotal /proc/meminfo

section "gpu"
for card in /sys/class/drm/card[0-9]; do
  [ -d "$card/device" ] || continue
  printf '%s vendor=%s device=%s driver=%s\n' "$(basename "$card")" \
    "$(cat "$card/device/vendor" 2>/dev/null)" "$(cat "$card/device/device" 2>/dev/null)" \
    "$(basename "$(readlink -f "$card/device/driver" 2>/dev/null)")"
done
if command -v lspci >/dev/null 2>&1; then
  lspci -nn | grep -Ei 'vga|display|3d' || true
fi

section "display"
for conn in /sys/class/drm/card*-*; do
  [ -r "$conn/status" ] || continue
  if [ "$(cat "$conn/status")" = "connected" ]; then
    printf '%s modes=%s\n' "$(basename "$conn")" "$(head -n 3 "$conn/modes" 2>/dev/null | tr '\n' ' ')"
  fi
done

section "power"
for bat in /sys/class/power_supply/BAT*; do
  [ -d "$bat" ] || continue
  printf '%s energy_full_design=%s voltage_min_design=%s charge_full_design=%s\n' "$(basename "$bat")" \
    "$(cat "$bat/energy_full_design" 2>/dev/null)" "$(cat "$bat/voltage_min_design" 2>/dev/null)" \
    "$(cat "$bat/charge_full_design" 2>/dev/null)"
done

section "os"
grep -E '^(ID|ID_LIKE|NAME|VERSION_ID|VERSION_CODENAME|BUILD_ID|VARIANT_ID)=' /etc/os-release
