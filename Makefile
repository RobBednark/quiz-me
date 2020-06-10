# To override variables from the command-line, use the make "-e" option,
# which causes environment variables to override assignments in the
# Makefile. e.g., 
#	make DB_NAME_DUMP='my-db'
#	PGDATABASE=template1  \
#   make \
#      FILE_DUMP_CUSTOM=db_dumps/my-dump-custom \
#      FILE_DUMP_PLAIN=db_dumps/my-dump-plain   \
#      loaddb
#	PGDATABASE=template1  make  FILE_DUMP_CUSTOM=db_dumps/my-dump-custom  FILE_DUMP_PLAIN=db_dumps/my-dump-plain  loaddb
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
DB_NAME_DUMP=restore_quizme_plain  # name of the db to dump
DB_NAME_RESTORE_CUSTOM=restore_quizme_custom
DB_NAME_RESTORE_PLAIN=restore_quizme_plain
DB_USER=quizme
DIR_DUMPS=db_dumps
date:=$(shell date "+%Y.%m.%d_%a_%H.%M.%S")
FILE_DUMP_CUSTOM:=${DIR_DUMPS}/dump.${DB_NAME}.${date}.custom
FILE_DUMP_PLAIN:=${DIR_DUMPS}/dump.${DB_NAME}.${date}.plain
FILE_DUMP_TEXT:=${DIR_DUMPS}/dump.${DB_NAME}.${date}.txt
SYMLINK_LATEST_TEXT:=${DIR_DUMPS}/latest.dump.txt

first_target:
	echo "This is the default target and it does nothing.  Specify a target."

create_superuser:
	./manage.py createsuperuser --email rbednark@gmail.com

createdb: 
	createdb --username=${DB_USER} ${DB_NAME_DUMP}

dropdb:
	dropdb ${DB_NAME_DUMP}

dumpdb: 
	mkdir -p db_dumps
	pg_dump --format=custom ${DB_NAME_DUMP} > ${FILE_DUMP_CUSTOM}
	pg_dump --format=plain ${DB_NAME_DUMP} > ${FILE_DUMP_PLAIN}
	./manage.py dump > ${FILE_DUMP_TEXT} 2>&1
	rm -f ${SYMLINK_LATEST_TEXT}
	ln -s `basename ${FILE_DUMP_TEXT}` ${SYMLINK_LATEST_TEXT}
	ls -ltr db_dumps/. |tail -5

flake8:
	flake8 --max-line-length=999

loaddb:
	# Load the dumps into new db's to test them
	psql --command="DROP DATABASE IF EXISTS ${DB_NAME_RESTORE_CUSTOM}"
	psql --command="DROP DATABASE IF EXISTS ${DB_NAME_RESTORE_PLAIN}"
	psql --command="CREATE DATABASE ${DB_NAME_RESTORE_CUSTOM}"
	psql --command="CREATE DATABASE ${DB_NAME_RESTORE_PLAIN}"

	pg_restore --dbname=${DB_NAME_RESTORE_CUSTOM} ${FILE_DUMP_CUSTOM}
	psql --user=${DB_USER} --dbname=${DB_NAME_RESTORE_PLAIN} --quiet --no-psqlrc < ${FILE_DUMP_PLAIN} > /tmp/psql.stdout

migrate:
	./manage.py migrate

recreatedb: dropdb createdb syncdb migrate create_superuser

recreate_migrations:
	rm -fr questions/migrations
	./manage.py schemamigration --initial questions
	# Add a dependency to the emailusername migration
	perl -pi -e 's/(class Migration\(SchemaMigration\):)/$$1\n    depends_on = \(\("emailusername", "0001_initial"\),\)/' questions/migrations/0001_initial.py

style-check: flake8
	
syncdb:
	./manage.py syncdb --noinput

test: test_phantomjs test_firefox

test_firefox:
	SELENIUM_BROWSER=firefox   ./manage.py test

test_nonbrowser:
	./manage.py test questions.tests.NonBrowserTests

test_phantomjs:
	SELENIUM_BROWSER=phantomjs ./manage.py test
