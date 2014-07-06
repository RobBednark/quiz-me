DB_NAME=quizme
DB_USER=quizme

create_superuser:
	./manage.py createsuperuser --noinput --email rbednark@gmail.com

createdb: 
	createdb --username=${DB_USER} ${DB_NAME}

dropdb:
	dropdb ${DB_NAME}

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
