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

self_file=$(readlink -f "$0") || error
self_dir=$(dirname "$self_file")

print_try 'rm -Rf "@ins_basedir@"'
print_try 'cp -Rf "'"$self_dir"'" "@ins_basedir@"'
print_try 'rm -f "@ins_basedir@/@rel_install@"'
print_try 'chown -R root:root "@ins_basedir@"'
print_try 'find "@ins_basedir@/" -type d | xargs chmod 755'
print_try 'find "@ins_basedir@/" -type f | xargs chmod 644'
print_try 'chmod 744 "@ins_basedir@/@rel_gui@"'
print_try 'chmod 755 "@ins_basedir@/@rel_bin@" "@ins_basedir@/@rel_uninstall@"'
print_try 'find "@ins_basedir@/@rel_scriptsdir@/" | xargs chmod 744'
print_try 'ln -fs "@ins_basedir@/@rel_desktop@" "@ins_desktop@"'
print_try 'ln -fs "@ins_basedir@/@rel_bin@" "@ins_bin@"'
for i in `ls "@ins_basedir@/@rel_iconsdir@"`
do
	size=`echo "$i" | awk -F . {'print $1'}`
	ext=`echo "$i" | awk -F . {'print $2'}`
	orig="@ins_basedir@/@rel_iconsdir@/$i"
	link="@ins_iconsdir@/$size/apps/@PACKAGE@.$ext"
	print_try "ln -fs \"$orig\" \"$link\""
done
print_try 'gtk-update-icon-cache -f -t "@ins_iconsdir@"'
print_try '"@ins_basedir@/@rel_bin@" -C'
print_try '"@ins_basedir@/@rel_bin@" --version'

