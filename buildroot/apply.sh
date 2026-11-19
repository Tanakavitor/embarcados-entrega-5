#!/bin/sh
# Usage: ./buildroot/apply.sh /path/to/buildroot
#
# 1. Cross-compiles hwctl and installs it into the overlay.
# 2. Points Buildroot's "Root filesystem overlay directories" at our overlay.
# 3. Enables the packages we need (python3, fswebcam, dropbear).
# Then just run: make ARCH=arm all   (inside the buildroot folder)
set -e

BR=${1:?usage: $0 /path/to/buildroot}
HERE=$(cd "$(dirname "$0")" && pwd)
OVERLAY="$HERE/overlay"

[ -f "$BR/.config" ] || { echo "$BR/.config not found: configure buildroot first (make ARCH=arm menuconfig)"; exit 1; }

if command -v arm-linux-gnueabihf-gcc >/dev/null; then
    make -C "$HERE/../hwctl" install
else
    echo "arm-linux-gnueabihf-gcc not in PATH: using prebuilt overlay/usr/bin/hwctl"
fi

# Kconfig keeps the last assignment of a symbol, so appending overrides older values.
{
    echo ""
    echo "# ---- Entrega 5 ----"
    echo "BR2_ROOTFS_OVERLAY=\"$OVERLAY\""
    grep -v '^#' "$HERE/entrega5.config" | grep -v '^$'
} >> "$BR/.config"

make -C "$BR" ARCH=arm olddefconfig

echo
echo "Buildroot configured. Check:"
grep -E '^BR2_ROOTFS_OVERLAY|^BR2_PACKAGE_(PYTHON3|FSWEBCAM|DROPBEAR)=' "$BR/.config"
echo
echo "Now run:  cd $BR && make ARCH=arm all -j\$(nproc)"
