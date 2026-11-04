#!/bin/sh
set -eu
myaac-entrypoint php /usr/local/bin/worldmap-menu.php
php /var/www/html/aac cache:clear
exec "$@"
