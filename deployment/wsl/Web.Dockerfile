FROM otbr-myaac:latest
COPY deployment/web/login.php /var/www/html/login.php
COPY deployment/web/plugins/ /var/www/html/plugins/
COPY deployment/wsl/worldmap.json /var/www/html/plugins/worldmap.json
COPY deployment/wsl/web-entrypoint.sh /usr/local/bin/canary-web-entrypoint
COPY deployment/wsl/worldmap-menu.php /usr/local/bin/worldmap-menu.php
COPY deployment/wsl/patch-myaac-status.php /tmp/patch-myaac-status.php
RUN php /tmp/patch-myaac-status.php && php -l /var/www/html/system/status.php && rm /tmp/patch-myaac-status.php && chmod +x /usr/local/bin/canary-web-entrypoint
ENTRYPOINT ["canary-web-entrypoint"]
CMD ["apache2-foreground"]
