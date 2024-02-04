#!/bin/sh

sed -e 's#^start #exec $app --dbus session #' 
