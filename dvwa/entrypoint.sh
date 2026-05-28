#!/bin/sh
set -e

DB_SERVER="${DB_SERVER:-127.0.0.1}"
DB_DATABASE="${DB_DATABASE:-dvwa}"
DB_USER="${DB_USER:-dvwa}"
DB_PASSWORD="${DB_PASSWORD:-dvwa}"
DB_PORT="${DB_PORT:-3306}"
DEFAULT_SECURITY_LEVEL="${DEFAULT_SECURITY_LEVEL:-low}"
DISABLE_AUTHENTICATION="${DISABLE_AUTHENTICATION:-false}"

mkdir -p /run/mysqld
chown -R mysql:mysql /run/mysqld /var/lib/mysql

if [ ! -d /var/lib/mysql/mysql ]; then
  mariadb-install-db --user=mysql --datadir=/var/lib/mysql --skip-test-db >/dev/null
fi

mysqld_safe --datadir=/var/lib/mysql --bind-address=127.0.0.1 &

until mysqladmin ping -h127.0.0.1 -P"${DB_PORT}" --silent; do
  sleep 2
done

mariadb -uroot <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_DATABASE}\`;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_DATABASE}\`.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON \`${DB_DATABASE}\`.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL

if ! mariadb -uroot "${DB_DATABASE}" -Nse "SHOW TABLES LIKE 'users';" | grep -q '^users$'; then
  mariadb -uroot "${DB_DATABASE}" < /usr/local/share/dvwa-init.sql
fi

if [ ! -f /var/www/html/config/config.inc.php ]; then
  cp /var/www/html/config/config.inc.php.dist /var/www/html/config/config.inc.php
fi

sed -i \
  -e "s/\$_DVWA\[ 'db_server' \].*/\$_DVWA[ 'db_server' ] = '${DB_SERVER}';/" \
  -e "s/\$_DVWA\[ 'db_database' \].*/\$_DVWA[ 'db_database' ] = '${DB_DATABASE}';/" \
  -e "s/\$_DVWA\[ 'db_user' \].*/\$_DVWA[ 'db_user' ] = '${DB_USER}';/" \
  -e "s/\$_DVWA\[ 'db_password' \].*/\$_DVWA[ 'db_password' ] = '${DB_PASSWORD}';/" \
  -e "s/\$_DVWA\[ 'db_port' \].*/\$_DVWA[ 'db_port' ] = '${DB_PORT}';/" \
  -e "s/\$_DVWA\[ 'default_security_level' \].*/\$_DVWA[ 'default_security_level' ] = '${DEFAULT_SECURITY_LEVEL}';/" \
  -e "s/\$_DVWA\[ 'disable_authentication' \].*/\$_DVWA[ 'disable_authentication' ] = ${DISABLE_AUTHENTICATION};/" \
  /var/www/html/config/config.inc.php

chown -R www-data:www-data /var/www/html/config /var/www/html/hackable/uploads
cp /var/www/html/config/config.inc.php /var/www/html/config/config.inc.php.bak

mkdir -p /var/log/apache2
rm -f \
  /var/log/apache2/access.log \
  /var/log/apache2/error.log \
  /var/log/apache2/other_vhosts_access.log
touch \
  /var/log/apache2/access.log \
  /var/log/apache2/error.log \
  /var/log/apache2/other_vhosts_access.log
if chown www-data:adm /var/log/apache2/*.log 2>/dev/null; then
  :
else
  chown www-data:www-data /var/log/apache2/*.log
fi
chmod 0644 /var/log/apache2/*.log

exec "$@"
