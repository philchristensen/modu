To set up your database to use this project, run the following queries:

CREATE DATABASE sandbox;
GRANT ALL ON sandbox.* TO sandbox@localhost IDENTIFIED BY 'sandbox';
FLUSH PRIVILEGES;

Then import the main schema file with:

mysql -u sandbox -p sandbox < docs/database-schema.mysql
