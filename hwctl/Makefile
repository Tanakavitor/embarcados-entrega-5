# Cross-compiles hwctl for the DE10-Standard HPS (ARM Cortex-A9).
# Static linking avoids glibc version mismatches with the Buildroot rootfs.
CROSS_COMPILE ?= arm-linux-gnueabihf-
CC = $(CROSS_COMPILE)gcc
CFLAGS ?= -O2 -Wall -Wextra -std=gnu99
LDFLAGS ?= -static
OVERLAY_BIN = ../buildroot/overlay/usr/bin

hwctl: hwctl.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

# Host build for testing the web UI on a PC (run with --mock)
hwctl-host: hwctl.c
	gcc -O2 -Wall -Wextra -std=gnu99 $< -o $@

install: hwctl
	install -D -m 0755 hwctl $(OVERLAY_BIN)/hwctl

clean:
	rm -f hwctl hwctl-host

.PHONY: install clean
