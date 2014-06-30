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

test:
	ROB_SELENIUM_BROWSER=phantomjs ./manage.py test
	ROB_SELENIUM_BROWSER=firefox   ./manage.py test
