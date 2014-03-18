#!/bin/bash

ns=$(netstat -ntupl) || exit $?

re=$(
	echo -n 's#^';
	echo -n '\(\s*\S*\)\{4\}:';
	# \2 : port
	echo -n '\([0-9]*\)\(\s*\S*\)\{2\}\s*';
	# \4 : pid
	echo -n '\([0-9]*\)/';
	# \5 : service
	echo -n '\(httpd\|mysqld\|proftpd\):*\s.*';
	# return 'service pid port'
	echo -n '$#\5 \4 \2#p';
)

echo "$ns" | sed -ne "$re" || exit $?

