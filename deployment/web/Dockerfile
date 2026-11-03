FROM php:8.3-apache-bookworm
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpng-dev libjpeg62-turbo-dev libfreetype6-dev libzip-dev libicu-dev \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j2 pdo_mysql gd zip intl \
 && a2enmod rewrite headers \
 && rm -rf /var/lib/apt/lists/*
COPY apache-canary.conf /etc/apache2/conf-available/canary.conf
COPY php-canary.ini /usr/local/etc/php/conf.d/canary.ini
RUN a2enconf canary
