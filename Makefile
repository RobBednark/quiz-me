DB_NAME=quizme
DB_USER=quizme

createdb: 
	createdb --username=${DB_USER} ${DB_NAME}

dropdb:
	dropdb ${DB_NAME}

migrate:
	./manage.py migrate

recreatedb: dropdb createdb syncdb migrate

syncdb:
	./manage.py syncdb --noinput

test: test_phantomjs test_firefox

test_firefox:
	ROB_SELENIUM_BROWSER=firefox   ./manage.py test

test_phantomjs:
	ROB_SELENIUM_BROWSER=phantomjs ./manage.py test
