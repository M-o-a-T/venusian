#!/bin/sh

sed -e 's#^start #exec $app --dbus session #' -e 's/dbus-send --system/dbus-send --session/'
