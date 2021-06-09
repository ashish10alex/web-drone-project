#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# read admin ips
ADMIN_IPS_OPTIONS="-a 127.0.0.1"
while read ip; do
	ADMIN_IPS_OPTIONS="$ADMIN_IPS_OPTIONS -a $ip"
done < $SCRIPT_DIR/admin_ips.txt

source $SCRIPT_DIR/bin/activate
pymushra server $ADMIN_IPS_OPTIONS
