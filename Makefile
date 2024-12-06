# To override variables from the command-line, use the make "-e" option,
# which causes environment variables to override assignments in the
# Makefile. e.g., 
#	make DB_NAME_TO_DUMP='my-db'
#
#	PGDATABASE=template1  \
#   make \
#      FILE_DUMP_CUSTOM=db_dumps/my-dump-custom \
#      FILE_DUMP_PLAIN=db_dumps/my-dump-plain   \
#      loaddb
#
#	PGDATABASE=template1  make  FILE_DUMP_CUSTOM=db_dumps/my-dump-custom  FILE_DUMP_PLAIN=db_dumps/my-dump-plain  loaddb
#
#   PGDATABASE=template1 make DB_NAME_TO_DUMP=quizme_production dumpdb
# 
# If restore fails due to a missing role, then create that role manually
# e.g., 
#    psql --command="CREATE USER my_user"
#
# To resolve an error like this:
#   psql: error: could not connect to server: FATAL:  database "rbednark" does not exist
# consider:
#   PGDATABASE=template1 make loaddb

SHELL := /bin/bash -xv

# The following variables that are not set to anything need to be set when calling make.
#    e.g., DB_NAME_TO_DUMP='my-db' make dumpdb
# DB_NAME_TO_DUMP = name of the db to dump
DB_NAME_TO_DUMP=
DB_NAME_TO_RESTORE_CUSTOM=restore_quizme_custom
DB_NAME_TO_RESTORE_PLAIN=restore_quizme_plain
# postgres://postgres:my_postgres_password@postgres:5432/quizme

DB_PORT=5432
DB_PASSWORD=
DB_SERVER=
DB_USER=
DB_CONNECTION_STRING:=postgres://${DB_USER}:${DB_PASSWORD}@${DB_SERVER}:${DB_PORT}/${DB_NAME_TO_DUMP}
DIR_DUMPS=db_dumps
FILE_DUMP_CUSTOM:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.custom.all
FILE_DUMP_DUMPDATA:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.dumpdata.json
FILE_DUMP_EXPORT_TAGS:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.export_tags.csv
FILE_DUMP_PLAIN_ALL:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.plain.all
FILE_DUMP_PLAIN_DATA:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.plain.data-only
FILE_DUMP_PLAIN_SCHEMA:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.plain.schema-only
FILE_DUMP_TEXT:=${DIR_DUMPS}/dump.${DB_NAME_TO_DUMP}.txt
USER_ID_EXPORT_TAGS=

first_target:
	echo "This is the default target and it does nothing.  Specify a target."

create_superuser:
	poetry run ./manage.py createsuperuser --email rbednark@gmail.com

createdb: 
	createdb --username=${DB_USER} ${DB_NAME_TO_DUMP}

dropdb:
	dropdb ${DB_NAME_TO_DUMP}

dumpdb: 
	test -n "$(DB_NAME_TO_DUMP)" || (echo 'error: DB_NAME_TO_DUMP not set'; false)
	test -n "$(DB_PASSWORD)" || (echo 'error: DB_PASSWORD not set'; false)
	test -n "$(DB_PORT)" || (echo 'error: DB_PORT not set'; false)
	test -n "$(DB_SERVER)" || (echo 'error: DB_SERVER not set'; false)
	test -n "$(DB_USER)" || (echo 'error: DB_USER not set'; false)
	rm -fr db_dumps
	mkdir -p db_dumps
	time pg_dump --format=custom ${DB_CONNECTION_STRING} > ${FILE_DUMP_CUSTOM}
	time pg_dump --format=plain  ${DB_CONNECTION_STRING} > ${FILE_DUMP_PLAIN_ALL}
	gzip ${FILE_DUMP_PLAIN_ALL}
	time pg_dump --data-only --format=plain ${DB_CONNECTION_STRING} > ${FILE_DUMP_PLAIN_DATA}
	gzip ${FILE_DUMP_PLAIN_DATA}
	time pg_dump --schema-only --format=plain ${DB_CONNECTION_STRING} > ${FILE_DUMP_PLAIN_SCHEMA}
	DB_QUIZME=${DB_NAME_TO_DUMP} PYTHONIOENCODING=utf-8 poetry run python ./manage.py dump > ${FILE_DUMP_TEXT} 2>&1
	DB_QUIZME=${DB_NAME_TO_DUMP} poetry run python ./manage.py export_tags --user-id=${USER_ID_EXPORT_TAGS} > ${FILE_DUMP_EXPORT_TAGS} 2>&1
	DB_QUIZME=${DB_NAME_TO_DUMP} poetry run python ./manage.py dumpdata --all --indent=2 > ${FILE_DUMP_DUMPDATA} 2>&1
	gzip ${FILE_DUMP_DUMPDATA}
	ls -hltr db_dumps/. |tail -8

flake8:
	flake8 --max-line-length=999

loaddb: loaddb-custom loaddb-plain

loaddb-custom:
	# Load the dumps into new db's to test them
	PGDATABASE=template1 psql --command="DROP DATABASE IF EXISTS ${DB_NAME_TO_RESTORE_CUSTOM}"
	PGDATABASE=template1 psql --command="CREATE DATABASE ${DB_NAME_TO_RESTORE_CUSTOM}"
	pg_restore --dbname=${DB_NAME_TO_RESTORE_CUSTOM} ${FILE_DUMP_CUSTOM}

loaddb-plain:
	# Load the dumps into new db's to test them
	PGDATABASE=template1 psql --command="DROP DATABASE IF EXISTS ${DB_NAME_TO_RESTORE_PLAIN}"
	PGDATABASE=template1 psql --command="CREATE DATABASE ${DB_NAME_TO_RESTORE_PLAIN}"
	PGDATABASE=template1 psql --user=${DB_USER} --dbname=${DB_NAME_TO_RESTORE_PLAIN} --quiet --no-psqlrc < ${FILE_DUMP_PLAIN}

migrate:
	poetry run ./manage.py migrate

recreatedb: dropdb createdb syncdb migrate create_superuser

recreate_migrations:
	rm -fr questions/migrations
	poetry run ./manage.py schemamigration --initial questions
	# Add a dependency to the emailusername migration
	perl -pi -e 's/(class Migration\(SchemaMigration\):)/$$1\n    depends_on = \(\("emailusername", "0001_initial"\),\)/' questions/migrations/0001_initial.py

style-check: flake8
	
syncdb:
	poetry run ./manage.py syncdb --noinput

test: 
	poetry run ./manage.py test
