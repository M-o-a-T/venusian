#!/bin/sh

sed -e 's#^start #exec $app --dbus session #' -e 's/dbus-send --system/dbus-send --session/' \ 
-e 's#/data/var/lib/mk2-dbus#/var/lib/venusian/venus/data/var/lib/mk2-dbus#' 
