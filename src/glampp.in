#!/bin/bash

if [ $(id -u) -ne 0 ]; then
	gksu "'$0' $@"
	exit $?
fi

###  ERROR  ###

zenity_escape()
{
	echo "$1" | sed -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/\(\W\)/\\\1/g'
}

error()
{
	head="@APPNAME@: $(zenity_escape "$1")"
	body=$(zenity_escape "$2")
	text="<span font=\"20\" font_weight=\"bold\">$head</span>\n\n$body"
	zenity --error --title="" --no-wrap --text="$text" 2> /dev/null \
	|| echo -e "$1: $2" >&2
	exit 1
}

###  PATHS  ###

self_file=$(readlink -f "$0") || error "Unexpected error" "readlink failed"
self_dir=$(dirname "$self_file")

gui_file="$self_dir/@rel_gui@"
config_file="$self_dir/@rel_config@"

###  CONFIG FILE  ###

print_default_config_file()
{
echo "$(cat <<'END_OF_DEFAULT_CONFIG'
[path]

lampp:         @def_lamppdir@

[command]

lampp:         %path_lampp%/lampp

start:         %command_lampp% start
startapache:   %command_lampp% startapache
startmysql:    %command_lampp% startmysql
startftp:      %command_lampp% startftp

stop:          %command_lampp% stop
stopapache:    %command_lampp% stopapache
stopmysql:     %command_lampp% stopmysql
stopftp:       %command_lampp% stopftp

reload:        %command_lampp% reload
reloadapache:  %command_lampp% reloadapache
reloadmysql:   %command_lampp% reloadmysql
reloadftp:     %command_lampp% reloadftp

restart:       %command_lampp% restart
security:      %command_lampp% security

enablessl:     %command_lampp% enablessl
disablessl:    %command_lampp% disablessl

backup:        %command_lampp% backup
oci8:          %command_lampp% oci8

status:        %path_scripts%/lampp_status.sh
END_OF_DEFAULT_CONFIG
)"
}

make_config_file()
{
	print_default_config_file > "$config_file"
	chown root:root "$config_file"
	chmod 644 "$config_file"
}

init_config_file()
{
	[ -f "$config_file" ] || make_config_file
}

###  VERSION  ###

print_version()
{
	echo '@APPNAME@ (@PACKAGE@) v@VERSION@ (@DATE@) @WEBSITE@'
}

###  OPTIONS  ###

usage()
{
cat <<EOF
Usage: @PACKAGE@ [params]
 --version : Print out package name and version and exit
 --help | -h : Print out this help message and exit
 --print-default-config | -c : Print out the default config file content
 --make-config | -C : Wipe config and create a new one using the default config
EOF
}

no_gui=''

while [ -n "$1" ]
do
	case $1 in
	--version) print_version; exit 0;;
	-h | --help) usage; exit 0;;
	-c | --print-default-config) print_default_config_file; no_gui=1; shift;;
	-C | --make-config) make_config_file; no_gui=1; shift;;
	'') shift;;
	*) usage; error "Parameter error" "Unknown option \"$1\"";;
	esac
done

[ -n "$no_gui" ] && exit 0

###  RUN GUI  ###

init_config_file

tmp_prefix="/tmp/$(date +%s%N)"
out_log="$tmp_prefix-log"
err_log="$tmp_prefix-log"
out_fifo="$tmp_prefix-out-fifo"
err_fifo="$tmp_prefix-err-fifo"
mkfifo "$out_fifo"
mkfifo "$err_fifo"
touch "$out_log" "$err_log"
log_pipe()
{
	cmd='echo "$1" >&'$1
	while read line; do
		sh -c "$cmd" +o "$line"
		echo "$line" >> "$2"
	done
}
cat "$out_fifo" | log_pipe 1 "$out_log" &
cat "$err_fifo" | log_pipe 2 "$err_log" &
"$gui_file" 2>"$err_fifo" > "$out_fifo"
exitcode=$?
out=$(cat "$out_log")
err=$(cat "$err_log")
rm -f "$out_fifo" "$err_fifo" "$out_log" "$err_log"
[ $exitcode -eq 0 ] || error "Unexpected error" "$err"

