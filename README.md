# Quiz-me: A memory reinforcement applicaton

## How to install and run
1. clone the repo
1. create a virtual environment using pipenv, e.g.,
        $ pipenv install
    or create a virtualenv using mkvirtualenv, e.g.,
        mkvirtualenv quizme
1. activate the virtualenv, e.g.,
        $ pipenv shell
    or using virtualenv:
        $ workon quizme
1. If using virtualenv instead of pipenv, install the required packages in the virtualenv, e.g.,
        pip install --requirement requirements.txt
1. install and run postgresql (if using postgresql); e.g., on OSX,
    brew install postgresql (or "brew update")
    ("brew info postgresql" to see how to start/stop)
    (if errors, consider "brew reinstall postgresql")
1. start postgres; e.g., on OSX,
    launchctl list | grep postgres  # see if launchctl knows about postgres, and if so, what the last exit status is
    brew services list  # list all running services, and see if postgresql is there
    brew services stop postgresql
1. create a postgres database
    createdb quizme
    (note that the database name "quizme" is a setting in settings.py for
     DATABASES['default']['NAME']
    )
1. create a postgres user:
    createuser quizme
    --or--
        psql --command="CREATE USER quizme"

    Test it:
        psql --user=quizme quizme
1. copy database
   --or--
   DB_QUIZME=my_db_name ./manage.py syncdb
   DB_QUIZME=my_db_name ./manage.py migrate
1. create a superuser
DB_QUIZME=my_db_name ./manage.py createsuperuser --email my_user@my_domain.com

## How to run tests

1. Install phantomjs: `brew cask install phantomjs`
2. Install geckodriver: `brew install geckodriver`
3. Install Firefox

### Docker Test Environment
I got some docker containers setup for with the intent of making local testing easier. In order to use it, you need to install docker and docker-compose, which is a util for managing sets of docker containers.

There are two config files involved with the docker testing containers:

```
Dockerfile
docker-compose.yml
```

The Django database settings also need to be modified. The best way to do that is by adding a `local_settings.py` file to the project's root directory with the following content:
```
DATABASES = {
'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'postgres',
    'USER': 'postgres',
    'HOST': 'db',
    'PORT': 5432,
    }
}
```

In order to get docker running the following commands need to be run from this project's root directory:

```
$ docker-compose up
$ docker-compose run web DB_QUIZME=my_db_name python manage.py syncdb
$ docker-compose run web DB_QUIZME=my_db_name python manage.py migrate
```

Django, Docker, and Pdb don't play well together. In order to set a stack trace inside some app code run docker-compose like so:

```
$ docker-compose run --service-ports web
```

I'm far from an expert on Docker in particular or containers in general. If something happens with a container and I don't know how to fix it I go nuclear, and then recreate everything. This command will stop and remove all containers.
```
docker rm $(docker ps -a -q)
```

## Development Conventions

* **merge commits**  
  All branch merges must have a merge commit (to make it clear when the branch changed), as opposed to a rebase, where there's no record of the rebase in git history.
* **merge commit message details**  
  For fixes, the message must detail what the bug is that has been fixed (include error text, etc.).  
  For new functionality, the message should describe the functionality; the following labels should be used to indicate what the commit does:  
      CHANGE, COMMENT, FIX, NEW, REFACTOR
* **manual testing for PR** -- each branch to be merged must have all manual tests run
* **manual test log**  -- manual testing for each branch or commit must be logged in TESTING.md
* **PEP8**  --code style must adhere to PEP8; PEP8 diversions are specified in tox.ini
* **granular commits**  
  All commits should be granular, e.g., a single (CHANGE, COMMENT, FIX, NEW, REFACTOR).  
  e.g., a single commit should not contain both fixes and features.
* **view &ast;.md changes before merging**   
  If changes are made to a markdown file (e.g., README.md), those changes should be viewed in a markdown editor (preferably github) before merging, to confirm that the formatting is correct

## Thoughts about scheduling
* maybe capture percentage of correctness and time since last seen
* I ask myself: when do I want to see this again?
* I ask myself: how long before I think I will forget this?
* consider assigning an importance to each question; distinguish between how important it is to me, and when I think I will forget it; don't mix the two together

## Show schedules for each tag

User > UserTag's > QuestionTag's > Question's > Schedule's > Schedule.date_added

Want: most recently-added Schedule for each Question for the specified User
To get latest Schedule's, need Question's and User
To get Question's, need QuestionTag's
To get QuestionTag's, need UserTag's (specifically, need the tag's from UserTag's to get the QuestionTag's)
To get UserTag's, need User

Reference: http://stackoverflow.com/questions/27544223/django-query-filter-many-to-many-to-many-etc
Reference: http://stackoverflow.com/questions/3630619/django-queryset-for-many-to-many-field

Could just add this code to _get_tag2periods, just need to add UserTag's.
Keep track of most-recently schedule question by seeing if that question has a UserTag (need an extra query for each question though)

Data structure to process schedules:
  questions2schedules[question_id] == latest_schedule

Iterate through questions for each tag:
    for tag in tags:
        questions = ...
        questions.annotate(newest_date_added)
        for question in questions:
            tag2periods...

Resulting data structure:
```
  tag2periods['python']['now-10m'] = 4
              ^^^^^^^^  ^^^^^^^^^    ^
              tag       period       num_questions
```

Consider using the Max(pk) to get the latest-added schedule.

Note that a question with multiple tags will still only have one schedule, because the schedule is per user per question.

Q: How do I find the most-recently-added schedule of each question (datetime_added)?
A: I have the queryset of questions.
*Get the code working first, then worry about performance.  Easier to just ask on stackoverflow with existing code.*

## Glossary / Terms / Nomenclature

**Table names**

* *answer* - answers to questions
* *attempt* -
    one question can have many attempts per user<br><br>

    fields:
        attempt.datetime_added - added, added_ts, when, when_added, ts_added, dt_added, *created

        attempt.datetime_updated - when_updated, *updated
        attempt.attempt
        attempt.text - the text the user typed in;
            body; corpus; paragraph; clob; stanza; input; representation

    brainstorming alternative names:
        trial?
        answer?
        given_answer?  user_answer (vs correct_answer)
        in_answer (incoming answer)
* *hint* - a hint for a question toward the answer
* *ignore* - ignore a question; never show it (alternative: hide)
* *question* - a question table
* *questiontag* - question id, get a representation of tags; junction table;
    one-to-many; find out what tags a given question has
* *quiz* - a set of tags, number of questions, options, ...
* *quiztag* - many-to-many; quiz_id, tag_id
* *?review? (verb)* - term for the act of using the program, of quizzing oneself, of reviewing flashcards
* *schedule* - for a question, the next time to ask that question again

    Alternatives:
        next_time_to_ask
        future
        when
        ask_again_time / ts / date / datetime
        appointment / future_appointment
        scheduled_at
        feedback
        output
        response
        Could response and schedule go together in the same table?
        interval_unit -- interval_value, interval

* *tag* - an arbitrary symbol associated with a question
* *usertag* - ??  tags added by users?

TODO: see if tables can be renamed in Django (eliminate the "questions_" prefix)

**Initial Glossary**
* answer - the "correct" answer associated with a question; a question can have 0 or 1 answers
* attempt - a user's single attempt to answer a question; it is the user's guess as to the answer
* hint - a hint for a question and answer (not yet implemented)
* schedule - when the user wants to see a question again
* question - a question
* quiz - a set of associated questions (not yet implemented)
* quiz - the name of the main Django app
* tag - a tag associated with a question; a question can have 0 to many tags
* user tag - the tags that a user has selected indicating which questions they want to see

## Tests
Tests to add:
* 12/27/14 add a test where there are no questions for whatever tags are selected, but selecting a different tag causes a question to be shown

## Notes
QuizMe notes can be found in these places:
* here (git repo /README)
* notebooks
* Portland Python quiz program (~/bin/learn/quiz.python/quiz.py)

*The rest of this file was moved from bin/learn/quiz.python/db/db_app_designs 9/16/13*

*Code: Dropbox/git/quizme_site*

## Documentation on various topics
question_next - ready (just a redirect to question)
question - shows a question with a form to input an attempt
    GET - show the question and an empty for for an attempt
    POST - post a new attempt
answer - shows the question, attempt, and answer, and a form to input a schedule
    GET - show the question, attempt, and answer
    POST - create a new schedule; redirect to question_next

Start request|Start template|User Action                           |End Request        |End template
-------------|--------------|--------------------------------------|-------------------|-------------------
(none)       |(none)        |user goes into quiz for the first time|GET /show_question/|show_question.html

GET /show_question/  show_question.html             user answers a question POST /show_question/  show_question_and_answer.html
POST /show_question/ show_question_and_answer.html  user clicks             GET /show_question/   show_question.html

### Requests, methods, and templates:
METHOD|REQUEST   |TEMPLATE REQUEST IS FROM  REQUEST VIA
------|----------|--------------------------------------------
GET   |/question/|question.html
POST  |/question/| 

### Symbolic actions:
* ask/show question (GET question)
* submit answer (POST question) (really POSTing an attempt)
* schedule question for next time (GET answer) (really GETting a specific attempt along with answer)
* submit answer feedback (POST answer) (really POSTing a schedule)

### Algorithm for deciding which question to show next:
* question has no schedule
* question has schedule with no interval

### Time zones
USE_TZ = True in the settings.py file, so time zone support is enabled.  Times are stored as UTC.
To get the current time in UTC, use:
    from django.utils import timezone
    now = timezone.now()
Note that:
    >>> naive = datetime.datetime.utcnow()
    >>> aware = timezone.now()
utcnow() is naive.

*See https://docs.djangoproject.com/en/1.7/topics/i18n/timezones/*

### HOW TO add a South migration
1. create the migration
```
./manage.py schemamigration myapp --auto
```
1. run the migration:
```
DB_QUIZME=my_db_name ./manage.py migrate myapp
```

### How to backup Postgres database and restore
Q: How to make a backup of the database?  
A:   
`make dumpdb`  
This creates dumps in 2 different formats (plain and custom) and puts them in the db_dumps subdir with a datestamp on them, e.g.,

```
-rw-r--r--  1 rob  staff  244938 Sep 26 17:26 dump.quizme.2014.09.26_Fri_17.26.21.plain
-rw-r--r--  1 rob  staff  125248 Sep 26 17:26 dump.quizme.2014.09.26_Fri_17.26.21.custom
```

Q: How to restore from a backup?  
A: 
`make loaddb`

This will create two databases named "restore_quizme_custom" and "restore_quizme_plain" and load the dumps.  They should each be identical, as the plain and custom dumps should each have the same data.

Q: How to restore a database manually?  
A:

```
DB_NAME_RESTORE_CUSTOM=restore_quizme_custom
FILE_DUMP_CUSTOM=~/Dropbox/git/quizme_website/db_dumps/dump.quizme.2016.09.04_Sun_10.01.32.custom
psql --dbname=postgres --command="DROP DATABASE IF EXISTS ${DB_NAME_RESTORE_CUSTOM}"
psql --dbname=postgres --command="CREATE DATABASE ${DB_NAME_RESTORE_CUSTOM}"
# Create role (what does it need to be?)
psql --dbname=postgres --command="CREATE USER rob"
pg_restore --verbose --dbname=${DB_NAME_RESTORE_CUSTOM} ${FILE_DUMP_CUSTOM} >& /tmp/pg_restore.out
psql --dbname=postgres --command="ALTER DATABASE ${DB_NAME_RESTORE_CUSTOM} RENAME TO quizme_master"
```
To get webapp to connect to that db:

```
    quizme_website/settings.py
        DATABASES
            'NAME': 'restore_quizme_custom'
```

## #TODO / #Backlog / #Features / #Stories
(NOTE: deprecate the Trello board and move the backlog items from https://trello.com/b/5WCzHwdo/quizme to here)

* 7.12.20 UPGRADE Upgrade splinter to the latest, using headless Chrome and/or Firefox instead of phantomjs
* 7.12.20 BUG If there is no valid session, when going to /login/?next=/question/ , it gives a 404 error instead of going to the login screen (this seems to happen when switching between databases, I don't know why).  WORKAROUND: navigate to the /admin page, it will prompt for login, login, and then you can access the question page
* 7.12.20 FEATURE consider a "frequency" field to indicate how often to see the flashcard (why? to show important/frequent cards that I want to see often, like daily, before other cards that are waiting to be seen before now) (e.g., show this card every 1 days, and if it hasn't been seen in the last day, then show it before other cards)
* 7.12.20 DEV_PROCESS update the release process to use github "releases" (why? to see release history, and see what was added when) (e.g., https://github.com/timmyomahony/django-pagedown/releases)
* 7.12.20 FEATURE prefill interval with values from previous schedule (why? to save time when reviewing)
* 7.12.20 FEATURE order by questions with answers first (why? to practice one's being learned)
* 7.12.20 FEATURE order by interval secs (amount of time scheduled to be seen again) (why? to practice what I am actively learning)
* 7/4/20, 3/28/15 allow a tree structure of tags, so that selecting a tag would select that and everything below it [suggested by Nev] (I discovered that I'm not reviewing as many flashcards because of not having this; e.g., select all non-software tags)
* 7/4/20 FEATURE: add db name to each web page
* 7/4/20 FEATURE: make question and answer editable while quizzing
* 7/4/20 FEATURE: optionally sort tags by date added, or just show the date added
* 6/24/20 FEATURE: when outputting dates, add the day-of-the-week, e.g. *__Tue__ June 23, 2020, 3:42 a.m.*
* 6/24/20 FEATURE: add *time_since_last_seen* field to schedule, e.g., the amount of time (secs, and maybe human-readable, and maybe previous date seen) between this response and the last response
* 6/24/20 FEATURE: add option to sort questions by number of times answered
* 6/24/20 FEATURE: put question and response in a single page, with the answer collapsed
* 6/24/20 FEATURE: show questions ordered by importance
* 6/24/20 FEATURE: add option to show unanswered questions first/last
* 6/24/20 FEATURE: add favorite or "like" percentage value for responses; similar to importance, but more for enjoyment of the question; add option to show questions sorted by "like"
* 9/14/16 STYLE: in list of tags, change the color of the tag if the tag is selected, to make it clear which are selected
* 9/11/16 FEATURE: For the selected tags, show them one per line right under "Tags selected:", along with num_questions and time periods, as is shown in the next section with all the tags.  As a user, I want to see these tags at the top and not have to hunt for them.
* 9/7/16 MODIFY: in the admin, modify it so that the width of the question/answer text isn't a single line and extremely wide
* 9/5/16 FEATURE: save the duration/interval to attempt table in the database; then show this duration for the answer, so the user can determine how well they did for the actual interval compared to the desired interval; also, consider adding query criteria for a quiz to say "show me all questions with an interval of less than 2 days"
* 9/5/16 FEATURE: for a quiz, make it possible to exclude questions with specified tags (e.g., quiz with all 'python' tags, except for questions that also contain the page 'web pages to review')
* 9/5/16 TEST: add tests for:
    - num_questions (for each tag)
    - each interval:
        - -now
        - 10m-1h
        - 1h-1d
        - 1d-1w
        - 1w-1mo
        - 1mo-1y
        - unseen
* 7/1/15 FEATURE: in addition to tags, consider keywords
* 6/28/15 FEATURE: show how long (duration/interval) it has been between when we last answered the question and now; this will me when I answer determine how long I want to set the next interval (both question and answer pages)
* 6/2/15 BUG: I added a new question with tags=[file_systems, unix]; when I went to quiz myself with a bunch of tags selected, but neither [file_systems, unix], I still got that question; after I answered that question, I then got another question with those same tags
  - it might be because the schedules query 
  - questions being shown that should not be:
        http://localhost:8000/question/1052/  
        http://localhost:8000/question/1053/
* 5/29/15 show list of selected tags on one line (instead of having to look through list of all tags) #high
* 05/17/15 show the number of questions recently answered/scheduled (e.g., 0-10mins=[5]  10-30mins=[12] 30m-2h=[4]  0-2h=[21])  #high
* 04/03/15 add a "note" section to the schedule, as a scratchpad, and also to mention what I forgot and what to remember next time  #high
* 3/10/15 don't allow duplicate tags to be created
* 3/10/15 show the question number on the answer page, so that it can be visually seen to manually edit the question in the admin
* Export (export questions via csv / json / yaml / xml / python data structure / plain text).  Find a way to maintain referential integrity.
* 02/11/15 On the answer page, add an input box where the user can type to practice the answer.  Maybe or maybe not save it (only value in saving it would be to see the effort that was made).  #high
* 01/23/15 Django Admin: be able to click on the answer from the list of questions page.
* 02/15/15 Django Admin: show the associated question(s) for each answer, and be able to click on the question 
* 01/23/15 Django Admin: add ability to edit answer in same page as editing question.
* 2/11/15  Show the schedule numbers for the total of selected tags (just like is done for each individual tag)  #high
* 01/23/15 Add search to Django admin to search in questions and answers.
* 12/31/14 Added schedule intervals for "immediate" and "never"
* 12/31/14 Allow a quiz mode that consists of a set of questions, and the user can go back and change their answers as much as they want (e.g., as part of an interview)
* 12/31/14 Make it possible to view questions that don't have any tags ("untagged")  #high
* 12/31/14 Have a "review all" mode that goes through all questions for the selected tags, showing you number seen and number remaining.
* 12/31/14 REFACTOR: change all datetime_* variables to either date_* or time_\*
* 12/31/14 Change all timezones to UTC
* 12/30/14 Implement variations (a question can have variations -- other questions that are similar but modified in a different way; e.g., 2+3=? could be a variation of 2+2=?); this is helpful so that you don't get in the habit of seeing the question and remembering the answer without understanding it
* 12/27/14 ask how well the question was answered (maybe percentage; excellent / good / bad)
* 12/21/14 Modify to pass question number in endpoint instead of as hidden field
* 12/21/14 Add contributors.md
* 12/21/14 Add to readthedocs
* 02/15/15 Consider adding a priority field (interval is ideally when you want to see it again, but priority is how important it is to you; so 2 different questions could have the same interval, but the one with the higher priority gets shown first; however, what to do if question1 has interval 1 month and priority "high", and question2 has interval 1 minute and priority "low" -- which gets shown first?)
* 12/21/14 Add tasks to either github issues or to Trello
* 11/17/14 add ability to select all or deselect all for tags  #high
* 10/20/14 add search ability, to search questions/answers for specified keywords
* 10/20/14 in the admin, when viewing a question, show the answer as an inline that can also be edited; likewise, when viewing an answer, show the question inline  #high
* 10/20/14 in the admin, when viewing a question, add a link/url to jump to the answer to view/edit it  #high
* 10/19/14 upgrade Django to latest (currently using 1.6.7; latest is 1.7)
* 10/18/14 per Steven Jonas, have a way to find other questions (or bookmarked webpages) with similar content to help form associations and new insights
* 10/18/14 have questions that are a single webpagge to review (a url), and show the content of the webpage instead of just a link
* 8/17/14 enabling tags during an answer does not enable it when the next question is shown (but it does work if enabled when asking a question)
* BUG: clicking on tag (to disable) during a question does not disable it when the answer is shown
* Show linefeeds as linefeeds for questions/answers/attempts (add <br/> tags; or add a rich text editor)
* 7/15/14 - add admin "list_filter" setting to be able to filter by tags on questions and answers
* use a single template: combine show_question.html and show_question_and_answer.html
* add an inline in the admin to edit the answer for a given question
* ability to change tags for the question shown #high
* Frequency (user selects when they want to see again (hr, day, 2 days, week, month, 2 mos)
* deploy to heroku
* 7/14/14 - add a "SKIP" button to skip a question
* 7/14/14 - capture the elapsed time that it took the user to reply
* 7/14/14 - show all questions/answers for given tags on a single page
* add documentation for other users to use
* FEATURE: display url's as clickable url's (href's) if they aren't already in markdown url format #high
* Import (import questions via csv / json / yaml / python data structure)
* Questions (add questions from the web page instead of the admin)
* Tags (be able to tag questions, and then select tags from which to select questions)
** DONE - select a single tag to use for a quiz
** DONE - select multiple tags to use for a quiz
*** consider allowing a hierarchy of tags, e.g.,
**** Programming
***** Languages
****** Python
****** Perl
****** C
***** Methodologies
****** Agile
*** Maybe allowing multiple parent/child relationships.
* NewUser registration
** page to create account
** email address verification/registration
* tests
* Footer: 
** show tags
** show how many times seen
** show how many times answered
** show last time seen
** show total number of questions
* Review mode: just show questions and answers
* email questions

* Rich Text for questions and answers
* graph database
* Questions (modify questions from the web page while asking the question)
* unique url's (e.g., either based on question words, or based on an id)
* "Ignore" tag -- never see the question again
* private questions/answers
* add Google Analytics

Front-end:
* ability to add questions/answers
* ability to modify questions/answers on-the-fly

* versions of questions/answers

* DONE - 8/29/14 Show the tags for the question being asked/answered.
* DONE - 3/10/15 show the answer id in answer.__unicode__ in the admin [DONE 3/10/15]
* DONE - 12/27/14 Show the number of questions for each tag (total number of questions, and number of questions past deadline)
* DONE - postgres backups (via Makefile)
* DONE - User login
* DONE - add tags via Django Admin

* Ask a question, and then show the answer.
** quiz view:
*** form:
**** if GET:
***** ask the first question
**** elif POST:
***** tell server which question was just asked
Format:
1. Show user a question
1. give user an input box to put their answer
1. Submit (user submits their answer)
1. save the user's answer, and show the correct answer, along with a Next button
1. Next (user clicks Next to go to the next question)
1. go to (1)
* Example of one answer with multiple questions:
    Q: 
    A:
* Example of one question with multiple answers:
    Q: 
    A:

### django-quiz
* Name of quiz is passed in the url
* views:
** question, answer, quiz, previous are all loaded in the context
* models:
** Category
** Quiz
** Progress
** Sitting
*** user
*** question_list (TextField; csv of questions)
*** incorrect_question (TextField; csv of incorrect questions)
** Question
** Answer

### User Stories / Features
* users can create accounts for themselves
* add questions via admin
* users can create quizzes (list of questions)
* Edit History (see history of edits of questions, etc.)
* web page is AJAX 
* users can edit other peoples questions/answers
* users can edit quizzes (add questions)
* users can edit quizzes (remove questions)
* users can add tags to questions
* users can add tags to questions during quiz
* can edit question while taking the quiz
* bulk upload
* edit a question while it's being asked
* edit an answer while it's being shown
* send emails with questions
* answer question in email
* view facts (no Q&A)
* algorithm based on Steven Jonas SuperMemo (Piotr Wozniak)
* spelling (sound clips)
* recognize photos
* time how long it takes to answer
* give Atlatl interview candidates quizzes
* ask in reverse (show answers, guess questions)
* study mode: show questions and answers together
* movie clips / YouTube videos

### Django Apps
Word meaning "piece of information":
chunk / game / info / piece of info / library / article / meme / agents / chapter / quiz / 
tidbit / interesting thing / atom / main / unit / info unit / knowledge / 
feature
segment
part
entity
noun
thing
bit
thing that stands alone
article
InfoEntity
component
portion
piece
fragment
building block
monad
constituent
entities

### MVP
Questions:
* text
Answers:
* text
Attempts:
* answer
* date
* user

### Entities
answers
hints
questions
quizzes (collection of questions)
tags
users

### Screens:
* New user (use the admin initially)
* Add a question/answer (use the admin initially)
* Edit a question/answer (use the admin initially)
* Quiz - ask questions, record answers

### Ultimate:
Question Types:
* multiple choice
* true/false
* fill in the blank
* essay
* audio clip
* video clip
* image
* click on photo (e.g., US map, states)
Hints:

Modes:

### Use Cases:
* want to quiz myself for a specify tag

## HOW TO use django-versioning
```
cddjango
cd learn_django-versioning_package
vim README
```

## Similar apps:
Anki - open source; written in Python; https://github.com/dae/anki
Brainscape (iOS)
Eidetic (iOS)
Flashcards (iOS)
Flashcardlet (iOS)
Fresh Memory - open source; Windows and Linux; last updated ; http://fresh-memory.com/ ; http://sourceforge.net/projects/freshmemory/; documentation last updated 10/6/14; app last updated 10/20/12; Mykhaylo Kopytonenko (mishakop at gmail com); c++
Mnemosyne
SuperMemo
Cram
Cram4Finals
Cramberry 
FlashBuddy
Flashcard Elite
Flashcards Deluxe
Fresh Memory
Mnemosyne
MyStudyPal
ProVoc
Quizlet
Repeat and Memorize
Study Stack
SuperMemo
http://www.flashcardapps.info/filter/

## Product/App Names / Naming:
### Name Ideas:
Ask Me
Ask Me Show Me

Brain Librarian
Brain Library

Capture and Memorize

Extra Memory

Fingertip
FlashCards
Fresh Memory (a Windows/Mac app with this name already exists)

Help Me Remember

I Remember

Learn and Remember
Learn-Quiz-Remember
LibraryOfQuestions

MeMemorize

Memorizer

Memory Aid
Memory Assistant
Memory Butler
Memory Chest
Memory Concierge
Memory Coach
Memory Curator
Memory Bunny
Memory Fountain
Memory-Go-Round
Memory Gym
Memory Lift
Memory Push-ups
Memory Refresh
Memory Refresher
Memory Secretary
Memory Toolchest
Memory Toy

Neuron Expander

Perfect Memory (French company website http://www.perfect-memory.com ; content management)

Quiz and Remember
QuizMe - already an iOS and Android app with this name
Quizzer
quizzical
QuizMeNow / quizmenow / quiz-me-now

Read Learn Quiz Remember
Read Quizi Learn Remember
Rediscover
Refresh My Memory (an Android app for remembering where you put things already exists)
Remember It
Review and Remember
Review to Remember

See If I Know
Show Me Again
Smart Quiz
So Many Questions
Spaced Repetition
Strong Memory
Sweet Memory

Tic-Tock-Remember
Time to Remember
Tip of my Tongue (iOS word-searching app with this name already exists)
Total Recall

What Was That?

### My Favorites:
Memory Butler
Memory Curator

### Keywords:
aid
ask
assistant
awesome
brain
butler
catalog
chest
clear
crisp
elephant
exercise
fit
fitness
flashcard
forget
genius
gray matter
gym
help
intelligent
learn
librarian
master
memorize
memory
muscle
neuron
pod
query
question
quiz
recall
remember
repeat
repetition
review
see
spaced repetition
storage
study
test
tool
workout

### Themes / analogies:
assistant
curation / collecting
exercise
memory
quiz
smart

### Naming ideas / considerations:
* use a two-part name (e.g., Evernote, Wunderlist, Tweetbot)
* use a strange name (e.g., Google, Yahoo)
* pronounceability
* 11 chars or less
* use a prefix or suffix (e.g., app, go, get) (e.g., outsideapp.com)
* check domain names
* account name availability on Facebook and Twitter
* easy to remember
* use real words with a twist (Ford Mustang)
* create a compound word
* make up a word
* add on a prefix (e.g., Coursera)
* add a pleasing word (e.g., Fountain)
    
### Taglines:
* Quizzes / Flashcards / Spaced Repetition

## Examples of tables
Attempt:

attempt |correct|question_id|datetime_added|datetime_updated|user_id
--------|-------|-----------|--------------|----------------|-------
"foobar"|True   |3          |7/1/14 8:35am |7/1/14 8:35am   |5

Question:

question|answer_id
--------|---------
1+1     |1

QuestionTag:

question_id|tag_id|enabled
-----------|------|-------
1          |1     |True

Tag:

name  |
------|
my_tag|

UserTag:

user_id|tag_id|enabled
-------|------|-------
1      |1     |True

For questions:
```
user_tags = UserTag.objects.filter(user=user, enabled=True)
question_tags = QuestionTag.objects.filter(enabled=True, tag__in=user_tags)
questions = Question.objects.filter(question__in=question_tags)
```

**The End... :)**
