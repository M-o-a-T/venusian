#!/bin/sh

sed -e 's#scriptdir=.*#scriptdir=/opt/victronenergy/gui#' -e 's/dbus-send --system/dbus-send --session/'
