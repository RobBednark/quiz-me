### Automated Tests
- all automated tests pass with postgres (make test)
- all automated tests pass with sqlite (make test)

### Development Process
- Review README *Development Conventions and Process* and confirm
### Schemas

- create copy of production db (quizme_restore_custom); apply migrations to it; test against it
    - `make DB_NAME_TO_DUMP=quizme_production dumpdb`
    - `make  FILE_DUMP_CUSTOM=db_dumps/restore.custom  FILE_DUMP_PLAIN=db_dumps/restore.plain  loaddb`
    - `python manage.py migrate`
    - `DB_QUIZME=restore_quizme_custom python manage.py runserver`

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