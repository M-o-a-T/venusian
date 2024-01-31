# The Venusian

"The Venusian" is a hybrid of Victron Energy's "venus" operating system for the
Raspberry Pi (and some others), and Debian GNU/Linux.

The Venusian allows you to run a Victron system on any Debian-based system.
This includes your Intel laptop.

This is of course impossible — but we're doing it anyway.

## Rationale

You might already have a Debian-based server in the same room as your Victron
installation, and yet another computer that nibbles away at your battery
isn't what you signed up for.

You might want to run code on your Victron system that won't work with
Python 8, or some other software that's not packaged for Victron's
OpenEmbedded installation. (NB, Python 8 is end-of-life in mid-2024.)

You might need a kernel module that the Victron kernel doesn't support.

You might want to re-use the backup solution you already have, instead of
coding some custom solution for Venus.

You might be interested in plugging a USB stick into your Venus
installation for RAID-0.

You might want to stop using the antiquated daemontools' supervisor and
runtime system because they don't talk to dbus or anything,
indiscriminately restart things which are broken or you don't need, and/or
don't send their logs anywhere.

… or maybe you just don't particularly like OpenEmbedded.


## Operation

Venus binaries run on the host system, using QEMU if necessary.

The Venus subsystem uses a session DBUS, not the system's.

They run as a "venus" user, not root.

The Venus system does *not* run inside a chroot environment, container, or whatever.

### OpenEmbedded libraries

Venus binaries is an `armhf` system and thus uses
`/lib/ld-linux-armhf.so.3` as its ELF loader.

The Venusian assumes that its host is not an `armhf` system (Raspberry Pi 3
and 4 run in 64-bit mode under Debian) and thus doesn't need to run any
other `armhf` binaries.

The Venusian hijacks this loader by patching the `/lib` and `/usr/lib`
strings that define its library search path, to `/v/l/` and `/v/u/lib`
respectively. Appropriate symlinks then ensure that the Venus binaries use
Venus libraries.

#### Alternate solution

If you do need to run non-Venus `armhf` binaries, we could alternately
patch all Venus binaries so they use a patched loader that's located
somewhere else.

Feel free to supply a script that does this.

### Venusian user

The Venusian system runs as the user `venusian`. It's controlled by a
user-level systemd instance and uses that user's session dbus instead of
the system's.

Thus, a simple `systemctl restart user@venus` restarts the whole Venus
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


### Multi-site operation 

It should be possible to run more than one Venus instance on the same host.

Details are TBD, TODO, and all that.


## Installation

The `install` script copies a current Venus image to a subvolume or
subdirectory of the host system and optionally customizes it.

The script accepts a couple of arguments. `dir`, `root` and `mount` are
mandatory.

### --image=/path/to/venus.img

The Venus image to copy onto your Debian system.

The file may be gzip-compressed.

### --dir=/path/to/dir

The destination for the Venus image.

### --root=/path/to/debian

The Debian system to install to. This may be the currently-running system.

### --mount=/mnt/venus

The directory which `/path/to/dir` will be bind-mounted to. This option defaults to 
`/mnt/venus`.

### --quiet

Don't blabber.

### --force

Don't skip existing files.

### --sub=WHAT

Also run the named scriptlets.

See the "Customization" section, below, for details.

### --help

Prints a summary of the options given above, as well as a list of possible
add-ons.

## File system considerations

The Venus file system should not be unpacked into the directory it's going
to be used at. Instead, the preferred strategy is to unpack it to some
other directory, then bind-mount the result.

This way, updates can be done in the background, requiring only a restart
of the Venus subsystem when finished — without rebooting the host
system.


## Customization

You can add your own customization steps to `install.d/NAME`. This
directory should contain bash scriptlets that are executed within
the `install` code.

### Scriptlets 

These customizer script names are known:

#### pre

#Runs first.

#### post

Runs last.

#### pkg-r

Packages to install in the root.

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
While we recommend not to do that, it's still good practice to quote
**all** uses of these variables.

#### Overlay file system

The installer may or may not create a complete copy of
`/opt/victronenergy`, the directory where Victron (sensibly) ships its code
in. In any case, `$OVER` contains the path to the destination file system,
which commonly is `$R/var/lib/venus/opt`.

Thus, a test whether to replace a file with its patched copy succeeds if
any of

* `$FORCE` is set
* the destination doesn't exist
* source and destination are the same file
* the source is newer

It should always `rm -f` the destination and `mkdir -p` any intermediate
directories.

The helper function `fchg ‹source› ‹dest›` does this for you. It exits with
return code 1 if you don't need to do anything. Otherwise the destination
is a new empty file.

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

