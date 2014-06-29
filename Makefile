DB_NAME=quizme
DB_USER=quizme

dropdb:
	dropdb ${DB_NAME}

createdb: 
	createdb --username=${DB_USER} ${DB_NAME}

recreatedb: dropdb createdb syncdb migrate

syncdb:
	./manage.py syncdb --noinput

migrate:
	./manage.py migrate


