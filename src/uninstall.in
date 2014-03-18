#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	gksu "'$0' $@"
	exit $?
fi

error()
{
	[ -n "$1" ] && echo "$1" 1>&2
	exit 1
}

print_try()
{
	echo "$1"
	sh -c "$1" || error
}

print_try 'rm -f "@ins_desktop@"'
find "@ins_iconsdir@" -lname "@ins_basedir@/@rel_iconsdir@/*" | while read i; do
	print_try "rm -f \"$i\""
done
print_try 'rm -Rf "@ins_basedir@"'
print_try 'gtk-update-icon-cache -f -t "@ins_iconsdir@"'
