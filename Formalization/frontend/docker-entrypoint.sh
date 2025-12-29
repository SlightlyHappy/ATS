#!/bin/sh

# Substitute environment variables in nginx configuration
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start nginx
exec "$@"
