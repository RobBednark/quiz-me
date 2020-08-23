# Quiz-me: A memory reinforcement applicaton

## How to install and run
1. clone the repo
1. create a virtual environment using pipenv, e.g.,

        $ pipenv install
    or create a virtualenv using mkvirtualenv, e.g.,

        $ mkvirtualenv quizme

1. activate the virtualenv, e.g.,

        $ pipenv shell
    or using virtualenv:

        $ workon quizme
1. If using virtualenv instead of pipenv, install the required packages in the virtualenv, e.g.,

        $ pip install --requirement requirements.txt
1. install and run postgresql (if using postgresql); e.g., on OSX,

        $ brew install postgresql (or "brew update")
    (`brew info postgresql` to see how to start/stop)
    (if errors, consider `brew reinstall postgresql`)
1. start postgres; e.g., on OSX,

        $ launchctl list | grep postgres  # see if launchctl knows about postgres, and if so, what the last exit status is

        $ brew services list  # list all running services, and see if postgresql is there
        $ brew services stop postgresql
1. create a postgres database, e.g.,

        $ createdb quizme
    (note that the database name "quizme" is a setting in `settings.py` for
     `DATABASES['default']['NAME']`
    )
1. create a postgres user:

        $ createuser quizme
    --or--

        $ psql --command="CREATE USER quizme"

    Test it:

        $ psql --user=quizme quizme
1. load existing data into database, or start with an empty database:

        $ DB_QUIZME=my_db_name ./manage.py syncdb
        $ DB_QUIZME=my_db_name ./manage.py migrate
1. create a superuser

        $ DB_QUIZME=my_db_name ./manage.py createsuperuser --email my_user@my_domain.com

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

## Development Conventions and Process

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
* **update README.md**
  Update README.md accordingly, including:  
    * TODO section -- remove corresponding item(s) if they have been implemented in this commit
* **update VERSION**  
  Update the version values in the questions/__version__.py file
* **update CHANGELOG**

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

### Time Zones
`USE_TZ = True` in the settings.py file, so time zone support is enabled.  Times are stored as UTC.  
To get the current time in UTC, use:

    from django.utils import timezone
    now = timezone.now()
Note that:

    >>> naive = datetime.datetime.utcnow()
    >>> aware = timezone.now()
utcnow() is naive.

*See https://docs.djangoproject.com/en/1.7/topics/i18n/timezones/*

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
(see **TODO.md** file)

### django-quiz
* Name of quiz is passed in the url
* views:
    * question, answer, quiz, previous are all loaded in the context
* models:
    * Category
    * Quiz
    * Progress
    * Sitting
        * user
        * question_list (TextField; csv of questions)
        * incorrect_question (TextField; csv of incorrect questions)
    * Question
    * Answer

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
```
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
```

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
- answers
- questions
- quizzes (collection of questions)
- tags
- users

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
- Anki - open source; written in Python; https://github.com/dae/anki
- Brainscape (iOS)
- Eidetic (iOS)
- Flashcards (iOS)
- Flashcardlet (iOS)
- Fresh Memory - open source; Windows and Linux; last updated ; http://fresh-memory.com/ ; http://sourceforge.net/projects/freshmemory/; documentation last updated 10/6/14; app last updated 10/20/12; Mykhaylo Kopytonenko (mishakop at gmail com); c++
- Mnemosyne
- SuperMemo
- Cram
- Cram4Finals
- Cramberry 
- FlashBuddy
- Flashcard Elite
- Flashcards Deluxe
- Fresh Memory
- Mnemosyne
- MyStudyPal
- ProVoc
- Quizlet
- Repeat and Memorize
- Study Stack
- SuperMemo
- http://www.flashcardapps.info/filter/

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
```
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
```

### Themes / analogies:
- assistant
- curation / collecting
- exercise
- memory
- quiz
- smart

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
