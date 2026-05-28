FROM php:8.2-apache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-mysql-client \
        git \
        libpng-dev \
        mariadb-server \
        netcat-openbsd \
    && docker-php-ext-install gd mysqli pdo pdo_mysql \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

RUN git clone --depth 1 https://github.com/digininja/DVWA.git . \
    && chown -R www-data:www-data /var/www/html

COPY entrypoint.sh /usr/local/bin/dvwa-entrypoint.sh
COPY dvwa-init.sql /usr/local/share/dvwa-init.sql

RUN chmod +x /usr/local/bin/dvwa-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["dvwa-entrypoint.sh"]
CMD ["apache2-foreground"]
