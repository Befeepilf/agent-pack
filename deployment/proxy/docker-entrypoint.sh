#!/bin/sh
set -eu
envsubst '${UPSTREAM}' < /etc/nginx/nginx.template > /etc/nginx/nginx.conf
exec nginx -g 'daemon off;' 