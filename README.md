# The Venusian

"The Venusian" is a hybrid of Victron Energy's "venus" operating system for the
Raspberry Pi (and some others), and Debian GNU/Linux.

The Venusian allows you to run a Victron system on any Debian-based system.
This includes your Intel laptop.

This is of course impossible — but we're doing it anyway.

**Warning**: The Venusian is not compatible with native ARMHF systems
(Raspberry Pi < 3, or 3/4 installed with 32-bit runtime).

**Warning**: After installing The Venusian, running or emulating non-Venus
ARMHF binaries will no longer work.


## Rationale

You might already have a Debian-based server in the same room as your Victron
installation, and yet another computer that nibbles away at your battery
isn't what you signed up for.

You might want to run code on your Victron system that requires Python
> 3.12, or some other software that's not packaged for Victron's
OpenEmbedded installation.

You might need a kernel module that the Victron kernel doesn't support.

You might want to re-use the backup solution you already have, instead of
coding some custom solution for Venus.

You might want to plug a USB stick into your Venus installation, for RAID.

You might want to stop using the antiquated daemontools' supervisor and
runtime system because they don't talk to dbus,
indiscriminately restart things which are broken or which you don't need,
and/or don't send their logs anywhere.

You might want to run more than one Venus installation on your server.

You might want to use hardware that doesn't lend itself to auto-detection
and don't want to fight the Venus system's autodiscovery.

… or maybe you just don't particularly like OpenEmbedded.


## Usage

* Install (see below).
* Optionally, `systemctl enable --now venusian-net`.
* `systemctl start venusian@venus`


### internal, bridged networking

__untested__

An internal bridged network is created; each Venus instance is attached to it,
starting with the PI address 192.168.42.1. IP address configuration via Venus
does *not* work.

This mode is used when `venusian-net` has been started.

You should be able to access Venus at http://your-machine/venusian/venus/
(assuming that you're using `nginx`).


### external, transparent networking

Your Venus instances use DHCP to retrieve an available IP address and behave
like "real" hardware.  (Static addresses are TODO.) IP address configuration via Venus
does *not yet* work.

This mode is used when `venusian-net` has *not* been started.

You should be able to access Venus at http://its-ip-address/. The address is
available via this command:

    /usr/lib/venusian/bin/ven -u venus ip -j -4 addr ls dev eth0 | jq -r 'first( .[] | .addr_info | .[] | select(.scope=="global") | select(.family=="inet") | .local )'


## Services

### MQTT

The Venus system includes a FlashMQ server, with a plug-in
that transparently gateways between DBus and MQTT.

This FlashMQ server runs once per user because the plug-in access the
Session DBus.

Integration of this MQTT server with the rest of your
installation works by bridging your main MQTT server to 
the server that's running in the Venus subsystem.
Autoconfiguration of this is TODO.


## Background

Venus binaries run on the host system, using QEMU if necessary.

The Venus subsystem uses a session DBUS, not the system's.

Its programs run as the user "venus", not root.

The Venus system does *not* run inside a chroot environment or a container.


### OpenEmbedded libraries

Venus is an `armhf` system (yes, even on Raspberry Pi 4); its binaries thus
use `/lib/ld-linux-armhf.so.3` as their ELF loader.

The Venusian assumes that its host is not an `armhf` system
and doesn't need to run any other `armhf` binaries.

The Venusian hijacks this `armhf` loader by patching the `/lib` and
`/usr/lib` strings that define its library search path, to `/v/l/` and
`/v/u/lib` respectively. Appropriate symlinks then ensure that the Venus
binaries use Venus libraries.

This means that your root directory will gain `/v` and `/data` entries.
Sorry about that; ways around this problem are being investigated.

We also need to add two symlinks to `/usr/lib` (`gconv` and `fonts`)
to convince `vedirect` and `gui` to not crash. These directories should not
exist on modern Debian systems, so there's no problem.


#### Alternate solution

If you do need to run non-Venus `armhf` binaries, we could alternately
modify the Venus binaries so their loader is in `/v/l/` instead of `/lib/`.

Patches welcome.


### Venusian user

The Venusian system runs as the user `venus`. It's controlled by a
user-level systemd instance and uses that user's session dbus instead of
the system's.

Thus, a simple `systemctl restart venusian@venus` restarts the whole Venus
subsystem cleanly, without requiring a possibly-risky reboot that takes an
order of magnitude longer and is much more disruptive.


### Devices ("udev")

Venus handles new serial devices by creating a symlink in /etc/serial-probe.
That directory is polled by a background process every two seconds. The
serial line is probed; if successful, the appropriate handler is created
and started via svc/demontools.

The Venusian considers this to be broken.

* Polling is bad. Don't do it.
* Many cheap adapters don't have serial numbers. You need to distinguish
  them somehow.
* Probing is time-consuming (multiple baud rates, protocols, device addresses
  on modbus, waiting for replies, starting multiple testers …).
* Probe messages can (and sometimes do) confuse the targets, esp. when sent
  at the "wrong" baud rate.
* There's no way to easily adjust the process, e.g. unconventional baud
  rates for Modbus/RTU.
* The probed device might be busy or booting up, thus not react in time.
* Devices that go away may or may not terminate the job started for them.

Our solution is different.

* New devices are handled by sending a message to a Unix socket.
  (Existing ones still use the symlink directory, for convenience.)
* The device handler reads a database of known devices, identified by serial
  number or bus position or whatnot. It then starts a systemd unit instance
  with the device (plus an opional parameter) as the instance name.
* Likewise, when a device goes away, its systemd unit is stopped.
* The program started by this, commonly a shell script, is responsible for
  executing whatever command the Victron probe system would have started.
* TODO: a helper to determine what the original serial prober would
  have done.

In practice, this means

### dbus-serialbattery

The Venusian optionally installs the "dbus-serialbattery" extension.

* Connect the serial line
* `udevadm info /dev/ttyUSB9`  # or whichever
* Add a matching entry to `/var/lib/venusian/udev.yml`, service=serialbattery
* Configure `/var/lib/venusian/venus/etc/serialbattery.cfg` appropriately
  (the defaults might work)
* `udevadm trigger /dev/ttyUSB9`  # or whichever

An isolated host adapter is probably a good idea.  A first approximation of whether
your adapter is engineered well is that udev reports a serial number that's not
all-zeroes (or 123456789).

#### Bluetooth

* `systemctl start venusian@venus`  # if not already running
* `vctl enable --now serialbattery-ble@Jkbms_Ble=XX:XX:XX:XX:XX:XX`

… except for the fact that Bluetooth isn't the most stable way to connect
a battery. Seriously: use RS485 instead.


### Multi-site operation 

It is possible to run more than one Venus instance on the same host,
mostly thanks to systemd magic that bind-mounts the `/var/lib/venusian/NAME`
directory to `/data`.

Venus' MQTT topics are prefixed by the output of `get-unique-id`, which
returns the system's UUID. We modify this script to include the user ID.


### Port redirects

The Venusian sets up a couple of `iptables` rules so that the user's MQTT
clients are served by its own MQTT server, not the system's.

As a side effect the user's MQTT server can't talk to the system server's
port 1883. The workaround is to teach the latter to also listen on port
51883.


## Installation

The `install` script copies a current Venus image to a subvolume or
subdirectory of the host system.

The script accepts a couple of arguments. `dir`, `root` and `mount` are
mandatory. You need to run it as root.

The Venus installation will be copied to the host system as-is. It won't
be modified.


### --image=/path/to/venus.img

The Venus image to use. Skip this option if you already unpacked or mounted
your Venus image.

The file may be gzip-compressed; in this case you'll need sufficient space
in /tmp for an uncompressed copy.

The special value "--image=-web-" downloads the current Venus version.
The image will be deleted after it's unpacked.


### --dest=/path/to/dir

The directory where you want to save (or did save) the Venus image to.
This option is mandatory unless you're creating a new Venusian user.

### --root=/path/to/debian

The Debian installation to install to. This may be the currently-running
system (use "/").

### --mount=/mnt/venus

The directory which `--dir` will be mounted to or accessible at.

This path is relative to `--root`.

If you skip this option *and* the root is `/`, the path from `--dir` will be used.
Otherwise you'll need to provide it.

### --quiet

Don't report print the script is doing (high-level).

### --verbose

Report shell commands as the installer executes them.

### --skip

Skip existing files. (By default, everything is overwritten.)

### --sub=WHAT

Also run the named add-on, stored in the directory `install.d/WHAT`.
This option may be used multiple times.

This allows you to customize the installation without modifying
the base script. See the "Customization" section, below, for details.

### --help

Prints a summary of the options given above, as well as a list of possible
add-ons.

## Plugins

### FlashMQ

This plugin installs a global FlashMQ process that can be used as an external gateway
to the Venusian FlashMQ.

The plugin creates a temporary file system for FlashMQ's persistent data if
you install to a chroot *or* `/var/lib` is on an SD-card ("`/dev/mmcblk…`").
This prevents excessive wear on the card's Flash memory. You might want to
periodically save this directory and restore it after rebooting.

### build

Install the tools required to compile software and build Debian packages.

Using this to build FlashMQ, instead of retrieving it externally, is TODO.

### fbset

Add code to configure the system's frame buffer so the Venus screen gets displayed on it.

Untested and most likely to be buggy.

### MoaT

(TODO)

## Installation errors

Note that the destination directory contains the *unmodified* Venus sources.
Any changes which the installer applies are done with an overlay directory.

### Unknown startup script

Read the script (in `$DEST/etc/rcS.d` or `$DEST/etc/rc5.d`) to check what it does.

Open the `install` script, find the line `### Startup scripts`. If it does
something The Venusian needs to replicate, write a service file and add it
to our `service` directory. Otherwise, simply add a do-nothing entry with
a short comment.

### Patch failures

The Venusian handles multiple versions of the Venus source files.
To handle a conflict:

* create a directory 'patchname.V' if necessary
* copy the old patch to 'patchname.V/vX.YZ' (with X.YZ being the last Venus
  release to which it applied cleanly)
* fix the patch
* commit the files to git, create a pull request


## Examples

### Raspberry Pi SD Card

Let's assume you have an SD card for a Raspberry Pi 4 you'd like to Venusianize.

* Copy a [Debian image](https://raspi.debian.net/tested-images/) to the card
* Plug into your computer; ensure that the card is **not** auto-mounted
* Use parted or fdisk to add a new partition at the end (1 GByte is sufficient)
* grow the second partition ("RASPIROOT") to fill all available space
* `resize2fs /dev/sdX2` (whichever sdX device your card is)
* `mkfs.ext4 -L VENUS /dev/sdX3`
* mount the partitions; we'll assume you use `/mnt/part2` as the target
* `install -i /tmp/venus.img.gz -d /mnt/part2 -r /mnt/venus
* Add `LABEL=VENUS /mnt/venusian ext4 none 0 2` to `/mnt/part2/etc/fstab`
* unmount, eject, plug into Raspberry Pi, etc..

### A typical server

* Use Debian >=13.
* `git clone https://github.com/M-o-a-T/venusian.git /opt/venusian`
* `cd /opt/venusian`
* `./install -i /tmp/venus.img.gz -d /opt/venus -r /
* systemctl start venusian@venus
* vncclient localhost:1


## helper scripts

All scripts are located in `/usr/lib/venusian/bin`. You can add this
directory to your path, or use shell aliases.

### get-unique-id

This is the script Venus uses to generate a unique ID, originally by using
the MAC address of `eth0`.

There are problems with this approach; some hosts don't have an `eth0`,
others might use a dynamic MAC for privacy. It's also not multi-user capable.

The Venusian uses a prefix of the machine ID and adds a the user ID (in hex).
You can add a "MACHID=XXX" line to `/etc/venusian/vars` or `/etc/venusian/NAME/vars`
if you want to override it. Note that the latter file includes the user ID.

### ven

`ven XXX` runs program `XXX` as the user "venus". You can use "-u NAME"
to switch to a different user.

This helper is required because a mere `sudo -u venus` doesn't connect you to
the user's DBus.

### vctl

Alias to `ven systemctl --user`. The "-u NAME" option is accepted.

### vbus

Alias to `ven dbus`. The "-u NAME" option is accepted.

"dbus" is a script from Victron that's much nicer than the
standard dbus-send program.


## Environment settings


## File system structure

The Venusian does not change the Venus file system. It needs to fix a
few minor problems, but that's with by an overlay file system.

We do however need to add a few symlinks to the file system's root, and to /usr.


## Customization

You can add your own customization steps to a directory `install.d/NAME`.
It should contain bash scriptlets that are executed within the `install` script.

### Scriptlets 

These customizer scriptlets are used:

#### pre

Runs first.

#### post

Runs last.

#### pkg-r

Packages to install in the root.

Add them to the `$I` variable. Please try to test whether they're already there,
because if so we can skip the time-consuming `apt` step.

#### lib

If this script is supplied, it replaces the built-in method that creates a
hacked-up copy of the armhf ELF loader. You could use this to implement the
"patch Venus" strategy, as mentioned above.


### Variables

* R: the destination Debian system's root
* V: the Venus subdirectory (a copy of the whole Venus image)
* MNT: the mountpoint of $V on $R, typically /mnt/venus
* LIBV: /var/lib/venus (the Victron user's home directory)
* USRV: /usr/lib/venusian (common helper files and scripts)
* SUBS: array of scriptlets to run
* OVER: the overlay file system
* FORCE: unconditionally replace things

Remember that all of these may contain spaces or other special characters.
While we recommend to use paths without whitespace, it's still good practice
to quote **all** uses of these variables.


#### Overlay file system

The installer does not create a complete copy of `/opt/victronenergy` (the
directory Victron ships its code in). Instead, an overlay file system is
used. `$OVER` contains the path to the "upper directory" of the overlay
file system that we use to selectively alter files.

However, this might change, as userspace overlays impose a certain
runtime overhead.

Thus, a test whether to replace a file with a patched version should succeed if
any of

* `$FORCE` is set
* the destination doesn't exist
* source and destination files are identical
* the source is newer

It should always `rm -f` the destination and `mkdir -p` any intermediate
directories.

The helper function `fchg ‹source› ‹dest›` does this for you. It exits with
return code 1 if you don't need to do anything. Otherwise the destination
is a new empty file.

The helper `fln` creates a symlink at ‹dest› that points to ‹source›.

The overlay file system is mounted with an `opt-victronenergy.mount` systemd unit.


## Changes to the host system

This section broadly documents the install script's changes to the host filesystem.

* create and populate $V (350 MBytes; small image as of 2024-01)
* create a user and group "venusian"
* mount its overlay file system at `/opt/victronenergy`
* populate its home directory in $LIBV
* create a patched `/lib/ld-linux-armhf.so.3`
* create a directory `/v` (with library symlinks, for the loader)
* create a symlink `/data` (to $LIBV)
* populate $USRV
* add udev scripts
* add helpers with hardcoded paths:
  * get-unique-id (uses the host's machine ID)

## TODOs

Last but definitely not least, this is a work in progess.

### Support for more battery managers, meters, and whatnot

There are sure to be some more incompatibilities.
Bug reports, patches and additional code gladly accepted.


### Clean up the Venus copy

Much of the original Venus file system is no longer required and can be deleted
to free some space. For instance, there's 60 MBytes of kernel modules,
60 MBytes of Python 3.8, 40 MBytes of opkg data, 15 MBytes of web server content,
and almost all of `/bin` and `/usr/bin`.

Original image's root file system: 350 MB, 100 MB compressed; cleaned up: around
70 MBytes, uncompressed.

### Documentation

This file is way too long.

### Installation

When installing a specific version, find the corresponding image. This is
not trivial because on Victron's server the file name has a timestamp along
with the file name.
