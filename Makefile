SHELL := /bin/bash
DB_NAME=quizme
DB_NAME_RESTORE_CUSTOM=restore_quizme_custom
DB_NAME_RESTORE_PLAIN=restore_quizme_plain
DB_USER=quizme
DIR_DUMPS=db_dumps
date:=$(shell date "+%Y.%m.%d_%a_%H.%M.%S")
FILE_DUMP_CUSTOM:=${DIR_DUMPS}/dump.${DB_NAME}.${date}.custom
FILE_DUMP_PLAIN:=${DIR_DUMPS}/dump.${DB_NAME}.${date}.plain

create_superuser:
	./manage.py createsuperuser --email rbednark@gmail.com

createdb: 
	createdb --username=${DB_USER} ${DB_NAME}

dropdb:
	dropdb ${DB_NAME}

dumpdb: 
	mkdir -p db_dumps
	pg_dump --format=custom ${DB_NAME} > ${FILE_DUMP_CUSTOM}
	pg_dump --format=plain ${DB_NAME} > ${FILE_DUMP_PLAIN}
	#pg_dump ${DB_NAME} > db_dumps/dump.${DB_NAME}.$(date).custom
	ls -ltr db_dumps/.

loaddb: dumpdb
	# Load the dumps into new db's to test them
	psql --command="DROP DATABASE IF EXISTS ${DB_NAME_RESTORE_CUSTOM}"
	psql --command="DROP DATABASE IF EXISTS ${DB_NAME_RESTORE_PLAIN}"
	psql --command="CREATE DATABASE ${DB_NAME_RESTORE_CUSTOM}"
	psql --command="CREATE DATABASE ${DB_NAME_RESTORE_PLAIN}"
	pg_restore --dbname=${DB_NAME_RESTORE_CUSTOM} ${FILE_DUMP_CUSTOM}
	psql --dbname=${DB_NAME_RESTORE_PLAIN} --quiet --no-psqlrc < ${FILE_DUMP_PLAIN}

migrate:
	./manage.py migrate

recreatedb: dropdb createdb syncdb migrate create_superuser

recreate_migrations:
	rm -fr questions/migrations
	./manage.py schemamigration --initial questions
	# Add a dependency to the emailusername migration
	perl -pi -e 's/(class Migration\(SchemaMigration\):)/$$1\n    depends_on = \(\("emailusername", "0001_initial"\),\)/' questions/migrations/0001_initial.py

syncdb:
	./manage.py syncdb --noinput

test: test_phantomjs test_firefox

test_firefox:
	ROB_SELENIUM_BROWSER=firefox   ./manage.py test

test_phantomjs:
	ROB_SELENIUM_BROWSER=phantomjs ./manage.py test
