## Manual tests to run:

*Run in dev environment*
- pipenv install --ignore-pipfile --dev

*Schemas*

- compare schemas between new db and production
- load production data into a new db using pg_dump and pg_restore/psql  
```
    dropdb quizme_new && createdb quizme_new
    DB_QUIZME=quizme_new python manage.py migrate
    PGDATABASE=template1 psql --user=quizme --dbname=quizme_new --quiet --no-psqlrc < dump.quizme_production.2020.06.26_Fri_18.04.57.plain.data-only
```
- create copy of production db (quizme_restore_custom); apply migrations to it; test against it


*Databases to run tests against*

- restored production db
- new postgresql db
- new sqlite db

*Tests*

- all automated tests pass (make test)

- logout
- login

- run quiz, answer question, submit a new schedule
- add a new question/answer
- run quiz and select a different tag to quiz on

- click the `Edit Question` link and edit a question
    - edit the text
    - add a tag
    - remove a tag
- click the `Edit Answer` link and edit the answer

- admin: questions page
- admin: tags page
- admin: Change tag name
- admin: answers page

- make dumpdb (ensure no errors)
- loaddb into a new db, then run all tests in this file against the new db
- compare prod schema to new schema

- python manage.py dump
- python manage.py makemigrations
- python manage.py showmigrations
- python manage.py migrate
- python manage.py migrate again (confirm no migrations needed)
- python manage.py showmigrations


## Test Log Template

What | Value
---- | -----
Date | 
Change summary | 
OS | 
firefox version | 
postgresql version (select version()) | 
python version | 
geckodriver version | 
phantomjs version | 
Pipfile lock used for manual tests | 
Pipfile lock used for automated tests | 

pip freeze:
```
```

## Test Log

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
