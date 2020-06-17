## Manual tests to run:

- dbs to run tests against:
    - restored production db
    - restored production db with migrations deleted
    - new postgresql db
    - sqlite db

- logout
- login
- run quiz, answer question, submit a new schedule
- add a new question/answer
- run quiz and select a different tag to quiz on
- click the `Edit Question` link and edit a question
    - edit the text
    - add a tag
    - remove a tag
- click the `Edit Answer` link and edit a question

- make dumpdb (ensure no errors)
- loaddb into a new db
    - run all tests in this file against the new db
- python manage.py dump
- python manage.py migrate

- create a new db, run "migrate", run manual tests

- admin: questions page
- admin: tags page
- admin: Change tag name
- admin: answers page

- all automated tests pass (make test)

## Test Log Template

Date: 
OS:  
firefox version: 
postgresql version:  
python version: 
geckodriver version: 
phantomjs version: 
Pipfile lock used for manual tests:  
Pipfile lock used for automated tests:  
pip freeze:

## Test Log

