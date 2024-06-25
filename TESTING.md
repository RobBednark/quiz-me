### Automated Tests
- all automated tests pass with postgres (make test)
- all automated tests pass with sqlite (make test)

### Development Process
- Review README *Development Conventions and Process* and confirm

### Run in dev environment
- `pipenv install --ignore-pipfile --dev`

### Schemas

- create copy of production db (quizme_restore_custom); apply migrations to it; test against it
    - `make DB_NAME_TO_DUMP=quizme_production dumpdb`
    - `make  FILE_DUMP_CUSTOM=db_dumps/restore.custom  FILE_DUMP_PLAIN=db_dumps/restore.plain  loaddb`
    - `python manage.py migrate`
    - `DB_QUIZME=restore_quizme_custom python manage.py runserver`


### Databases to run tests against

- production db (or restored production db)
- new postgresql db
- new sqlite db

### Manual Tests


- `DB_QUIZME=my_sqlite_db QM_ENGINE=sqlite DJANGO_SUPERUSER_USERNAME=rbednark DJANGO_SUPERUSER_EMAIL=my_user@my_domain.com DJANGO_SUPERUSER_PASSWORD=p ./manage.py createsuperuser --no-input`
- logout
- login

- review with no questions, no tags, and confirm that behavior is correct (allows changing tags):
    1. confirm there are no questions
    2. GET /flashcard (confirm message indicating no questions; confirm tags section is open with no tags)
    3. add a question with a tag
    4. GET /flashcard (confirm message indicating no questions; confirm tags section is open with a tag)
    5. select the tag and submit
    6. confirm question is shown, and there are no errors shown
    7. submit (confirm no errors, and that question is shown again)
- run quiz, answer question, submit a new schedule
- add a new question/answer
- run quiz and select a different tag to quiz on

- click the `Edit Question` link and edit a question
    - edit the text
    - add a tag
    - remove a tag
- click the `Edit Answer` link and edit the answer

- admin: Answers page
- admin: Attempts page
- admin: Questions page
- admin: Schedules page
- admin: Tags page
- admin: Tags page: change tag name

- `make dumpdb` (ensure no errors)
- loaddb into a new db, then run all tests in this file against the new db
- compare prod schema to new schema
    - for new db and production:
        `make DB_NAME_TO_DUMP=... dumpdb `
    - diff the schema-only files

- `python manage.py dump`
- `python manage.py makemigrations`
- `python manage.py showmigrations`
- `python manage.py migrate`
- `python manage.py migrate` again (confirm no migrations needed)
- `python manage.py showmigrations`

- `./manage.py dumpdata --all | jq > /tmp/dumpdata`
- `./manage.py loaddata /tmp/dumpdata` (into a new postgres db)
    - `runserver` and poke around
- `./manage.py loaddata /tmp/dumpdata` (into a new sqlite db)
    - `runserver` and poke around


## Test Log Template

----

What | Value
---- | -----
Date | 
Change summary | 
OS | 
chrome version | 
firefox version | 
postgresql version (select version()) | 
python version | 
geckodriver version | 
phantomjs version | 

pip freeze:
```
```

## Test Log

----

What | Value
---- | -----
Date | 14 Jul 2020 Tue
Change summary | Upgrade all packages to latest, including Django 2 to 3
OS |  macOS Mojave 10.14.6 (kernel 18.7.0)  
chrome version | 83.0.4103.116
firefox version | 78.0.2
postgresql version (select version()) | 12.3
python version | 3.7.7
geckodriver version | 0.26.0
phantomjs version | 2.1.1

pip freeze:
```
asgiref==3.2.10
Django==3.0.8
django-markdown-deux==1.0.5
django-pagedown==2.1.2
markdown2==2.3.9
Pillow==7.2.0
psycopg2==2.8.5
py2-py3-django-email-as-username==1.7.1
python-dateutil==2.8.1
pytz==2020.1
selenium==3.141.0
six==1.15.0
splinter==0.8.0
sqlparse==0.3.1
urllib3==1.25.9
```

*Automated Tests*
- PASS all automated tests pass with postgres (make test)
- PASS all automated tests pass with sqlite (make test)

## Manual tests to run:

*Run in dev environment*
- DONE pipenv install --ignore-pipfile --dev

*Schemas*

- PASS create copy of production db (quizme_restore_custom); apply migrations to it; test against it
    - PASS make DB_NAME_TO_DUMP=quizme_production dumpdb
    - PASS make  FILE_DUMP_CUSTOM=db_dumps/restore.custom  FILE_DUMP_PLAIN=db_dumps/restore.plain  loaddb
    - PASS python manage.py migrate
    - PASS DB_QUIZME=restore_quizme_custom python manage.py runserver


*Databases to run tests against*

- PASS production db (or restored production db)
- PASS new postgresql db
- PASS new sqlite db

*Manual Tests* (production db)
- SKIP DB_QUIZME=my_sqlite_db QM_ENGINE=sqlite DJANGO_SUPERUSER_USERNAME=rbednark DJANGO_SUPERUSER_EMAIL=my_user@my_domain.com DJANGO_SUPERUSER_PASSWORD=p ./manage.py createsuperuser --no-input
- PASS logout
- PASS login

- PASS run quiz, answer question, submit a new schedule
- PASS add a new question/answer
- PASS run quiz and select a different tag to quiz on

- PASS click the `Edit Question` link and edit a question
    - PASS edit the text
    - SKIP add a tag
    - SKIP remove a tag
- PASS click the `Edit Answer` link and edit the answer

- PASS admin: Answers page
- admin: Attempts page
- PASS admin: Questions page
- admin: Schedules page
- PASS admin: Tags page
- PASS admin: Tags page: change tag name

- PASS make dumpdb (ensure no errors)
- SKIP loaddb into a new db, then run all tests in this file against the new db
- DONE compare prod schema to new schema
    - for new db and production:
        PASS make DB_NAME_TO_DUMP=... dumpdb 
    - PASS diff the schema-only files; differences:
        - field ordering (e.g., "user_id integer")
        - CREATE SEQUENCE -- add "as integer"
        - constraints have different names
        - indexes have different names (unique name)


- PASS python manage.py dump
- PASS python manage.py makemigrations
- PASS python manage.py showmigrations
- PASS python manage.py migrate
- PASS python manage.py migrate again (confirm no migrations needed)
- PASS python manage.py showmigrations

*Manual Tests* (new postgresql db) 
- PASS DB_QUIZME=quizme_new QM_ENGINE=postgres DJANGO_SUPERUSER_USERNAME=rbednark DJANGO_SUPERUSER_EMAIL=my_user@my_domain.com DJANGO_SUPERUSER_PASSWORD=p ./manage.py createsuperuser --no-input
- PASS logout
- PASS login

- PASS run quiz, answer question, submit a new schedule
- PASS add a new question/answer
- PASS run quiz and select a different tag to quiz on

- PASS click the `Edit Question` link and edit a question
    - PASS edit the text
    - PASS add a tag
    - PASS remove a tag
- PASS click the `Edit Answer` link and edit the answer

- PASS admin: Answers page
- PASS admin: Attempts page
- PASS admin: Questions page
- PASS admin: Schedules page
- PASS admin: Tags page
- SKIP admin: Tags page: change tag name


- PASS make dumpdb (ensure no errors)
- SKIP loaddb into a new db, then run all tests in this file against the new db
- DONE compare prod schema to new schema (see above)

- PASS python manage.py dump
- PASS python manage.py makemigrations
- PASS python manage.py showmigrations
- PASS python manage.py migrate
- PASS python manage.py migrate again (confirm no migrations needed)
- PASS python manage.py showmigrations

*Manual Tests* (new sqlite db) 

- PASS DB_QUIZME=my_sqlite_db QM_ENGINE=sqlite DJANGO_SUPERUSER_USERNAME=rbednark DJANGO_SUPERUSER_EMAIL=my_user@my_domain.com DJANGO_SUPERUSER_PASSWORD=p ./manage.py createsuperuser --no-input
- PASS logout
- PASS login

- PASS run quiz, answer question, submit a new schedule
- PASS add a new question/answer
- PASS run quiz and select a different tag to quiz on

- PASS click the `Edit Question` link and edit a question
    - PASS edit the text
    - PASS add a tag
    - PASS remove a tag
- PASS click the `Edit Answer` link and edit the answer

- PASS admin: Answers page
- PASS admin: Attempts page
- PASS admin: Questions page
- PASS admin: Schedules page
- PASS admin: Tags page
- PASS admin: Tags page: change tag name


- SKIP make dumpdb (ensure no errors)
- SKIP loaddb into a new db, then run all tests in this file against the new db
- SKIP compare prod schema to new schema

- PASS python manage.py dump
- PASS python manage.py makemigrations
- PASS python manage.py showmigrations
- PASS python manage.py migrate
- PASS python manage.py migrate again (confirm no migrations needed)
- PASS python manage.py showmigrations

- PASS ./manage.py dumpdata --all | jq > /tmp/dumpdata
- PASS ./manage.py loaddata /tmp/dumpdata (into a new postgres db)
    - PASS runserver and poke around
- PASS ./manage.py loaddata /tmp/dumpdata (into a new sqlite db)
    - PASS runserver and poke around



----

What | Value
---- | -----
Date | Mon 7.6.20
Change summary | Change _get_next_question() algorithm
OS |  macOS Mojave 10.14.6 (kernel 18.7.0)  
firefox version | 77.0.1
postgresql version (select version()) | 12.3
python version | 3.7.7
geckodriver version | 0.26.0
phantomjs version | 2.1.1

pip freeze:
```
Django==2.0.3
django-markdown-deux==1.0.5
django-pagedown==1.0.4
markdown2==2.3.5
psycopg2==2.7.4
pudb==2019.2
py2-py3-django-email-as-username==1.7.1
Pygments==2.6.1
python-dateutil==2.7.2
pytz==2018.3
selenium==3.141.0
six==1.11.0
splinter==0.8.0
urllib3==1.25.9
urwid==2.1.0
```

DONE *Run in dev environment*
- DONE pipenv install --ignore-pipfile --dev

DONE *Schemas*

- SKIP compare schemas between new db and production
- DONE create copy of production db (quizme_restore_custom); apply migrations to it; test against it
    - DONE make DB_NAME_TO_DUMP=quizme_production dumpdb
    - DONE make  FILE_DUMP_CUSTOM=db_dumps/restore.custom  FILE_DUMP_PLAIN=db_dumps/restore.plain  loaddb
    - DONE python manage.py migrate
    - DONE DB_QUIZME=restore_quizme_custom python manage.py runserver

*Databases to run tests against*

- production db (or restored production db)
- SKIP new postgresql db
    - skipped because production db testing is good enough; this PR is read-only changes
- SKIP new sqlite db
    - not working due to Django issue mentioned below in previous test run

*Tests* (production db)

- PASS logout
- PASS login

- PASS run quiz, answer question, submit a new schedule
- PASS add a new question/answer
- PASS run quiz and select a different tag to quiz on

- PASS click the `Edit Question` link and edit a question
    - PASS edit the text
    - SKIP add a tag
    - SKIP remove a tag
- SKIP click the `Edit Answer` link and edit the answer

- PASS admin: questions page
- PASS admin: tags page
- PASS admin: Change tag name
- PASS admin: answers page

- PASS make dumpdb (ensure no errors)
- SKIP loaddb into a new db, then run all tests in this file against the new db
    - Skipped because low risk of this regressing.
- SKIP compare prod schema to new schema
    - No new migrations in this PR.

- PASS python manage.py dump
- PASS python manage.py makemigrations
- PASS python manage.py showmigrations
- PASS python manage.py migrate
- PASS python manage.py migrate again (confirm no migrations needed)
- PASS python manage.py showmigrations

--------------------------------------------------------------------------------

What|Value
----|-----
Date | 6.25.20 Wed 1:30pm
Change summary | Upgrade to Django 2.0  
OS |  macOS Mojave 10.14.6 (kernel 18.7.0)  
chrome version |  83.0.4103.116 up-to-date  
firefox version | 77.0.1 up-to-date 
postgresql version (select version()) | 12.3  
python version | 3.7.7  
geckodriver version | 0.26.0  
phantomjs version | 2.1.1  

pip freeze:
```
  Django==2.0.3
  django-markdown-deux==1.0.5
  django-pagedown==1.0.4
  markdown2==2.3.5
  psycopg2==2.7.4
  py2-py3-django-email-as-username==1.7.1
  python-dateutil==2.7.2
  pytz==2018.3
  selenium==3.141.0
  six==1.11.0
  splinter==0.8.0
  urllib3==1.25.9
```

*Notes*

- DONE pipenv install --ignore-pipfile --dev
- DONE compare schemas between production and new db
    - differences:
        - south tables removed (not an issue)
        - field ordering (not an issue)
        - id key names (I doubt it's an issue)
        - index names (I doubt it's an issue)
- DONE load production data into a new db using pg_dump and pg_restore/psql  
    NOTE: the COPY command stops operation at the first error.
    - There were 7 errors:
```
        ERROR:  duplicate key value violates unique constraint "django_content_type_pkey"
        DETAIL:  Key (id)=(1) already exists.
        CONTEXT:  COPY django_content_type, line 1

        ERROR:  duplicate key value violates unique constraint "auth_permission_pkey"
        DETAIL:  Key (id)=(1) already exists.
        CONTEXT:  COPY auth_permission, line 1

        ERROR:  insert or update on table "django_admin_log" violates foreign key constraint "django_admin_log_user_id_c564eba6_fk_emailusername_user_id"
        DETAIL:  Key (user_id)=(1) is not present in table "emailusername_user".

        ERROR:  duplicate key value violates unique constraint "django_migrations_pkey"
        DETAIL:  Key (id)=(1) already exists.
        CONTEXT:  COPY django_migrations, line 1

        ERROR:  duplicate key value violates unique constraint "django_site_pkey"
        DETAIL:  Key (id)=(1) already exists.
        CONTEXT:  COPY django_site, line 1

        ERROR:  relation "public.south_migrationhistory" does not exist
        invalid command \.
        ERROR:  syntax error at or near "1"
        LINE 1: 1 emailusername 0001_initial 2014-07-06 13:59:28.894109-07

        ERROR:  relation "public.south_migrationhistory_id_seq" does not exist
        LINE 1: SELECT pg_catalog.setval('public.south_migrationhistory_id_s...
```
- DONE compare data in django tables between production and new db
        - django_content_type
            - insignficant: new db has one less row (south); this means the id's for rows 8-17 are all one less
        - auth_permission
            - insignficant: new db has 3 fewer rows (48 instead of 51):
                - add/change/delete migrationhistory
        - django_migrations
            - insignficant: naturally different; e.g., new db doesn't have migrations that I deleted; pretty similar though
        - django_site
            - identical (just one row with example.com)
        - django_admin_log
            - insignficant: new db has no rows
            ERROR:  insert or update on table "django_admin_log" violates foreign key constraint "django_admin_log_user_id_c564eba6_fk_emailusername_user_id"
            DETAIL:  Key (user_id)=(1) is not present in table "emailusername_user".

            It loaded the row.  This is an ordering issue.  Reorder and try again.
            I reordered.  Now I get:
                ERROR:  insert or update on table "django_admin_log" violates foreign key constraint "django_admin_log_content_type_id_c4bce8eb_fk_django_co"
                DETAIL:  Key (content_type_id)=(17) is not present in table "django_content_type".
            This is because django_content_type has different rows
    

- dbs to run tests against:
    - PASS - restored production db
    - PASS - new postgresql db
    - FAIL - sqlite db

*Testing against: new sqlite db*

- FAIL - adding tag:
```
    OperationalError at /admin/questions/tag/add/
    no such table: main.django_content_type__old
```
This is fixed in Django 2.1.5

*Testing against: new postgresql db (new_quizme)*

- DONE - pipenv install --ignore-pipfile --dev
- PASS - logout
- PASS - login
- PASS - run quiz, answer question, submit a new schedule
- PASS - add a new question/answer
- PASS - run quiz and select a different tag to quiz on
- PASS - click the `Edit Question` link and edit a question
    - PASS - edit the text
    - PASS - add a tag
    - PASS - remove a tag
- PASS - click the `Edit Answer` link and edit the answer

- PASS - make dumpdb (ensure no errors)
- PASS - loaddb into a new db (restore_quizme_custom)
- PASS - python manage.py dump
- PASS - python manage.py makemigrations
- PASS - python manage.py migrate
- PASS - python manage.py migrate again (confirm no migrations needed)
- PASS - python manage.py showmigrations

- PASS - admin: questions page
- PASS - admin: tags page
- PASS - admin: Change tag name
- PASS - admin: answers page

- PASS - all automated tests pass (make test)



*Testing against: restored production db (restore_quizme_custom)*

- PASS - logout
- PASS - login
- PASS - run quiz, answer question, submit a new schedule
- PASS - add a new question/answer
- PASS - run quiz and select a different tag to quiz on
- PASS - click the `Edit Question` link and edit a question
    - PASS - edit the text
    - PASS - add a tag
    - PASS - remove a tag
- PASS - click the `Edit Answer` link and edit a question

- PASS - make dumpdb (ensure no errors)
- PASS - loaddb into a new db
    - PASS - run all tests in this file against the new db
- PASS - python manage.py dump
- PASS - python manage.py makemigrations
- PASS - python manage.py migrate
- PASS - python manage.py migrate again (confirm no migrations needed)
- PASS - python manage.py showmigrations

- PASS - admin: questions page
- PASS - admin: tags page
- PASS - admin: Change tag name
- PASS - admin: answers page

- PASS - all automated tests pass (make test)
