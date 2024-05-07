#!/usr/bin/env bash

set -euvx
date
pwd
git status
git show --no-patch
git log --max-count=4

DB_QUIZME=${DB_QUIZME:?'ERROR: shell variable DB_QUIZME must be set'}
DB_USER=${DB_USER:?ERROR: shell variable DB_USER must be set}
QM_DB_HOST=${QM_DB_HOST:?ERROR: shell variable QM_DB_HOST must be set}
QM_DB_PASSWORD=${QM_DB_PASSWORD:?ERROR: shell variable QM_DB_PASSWORD must be set}
QM_DEBUG=${QM_DEBUG:=False}
QM_INCLUDE_UNANSWERED=${QM_INCLUDE_UNANSWERED:=True}
QM_LIMIT_TO_DATE_SHOW_NEXT_BEFORE_NOW=${QM_LIMIT_TO_DATE_SHOW_NEXT_BEFORE_NOW:=True}
QM_NULLS_FIRST=${QM_NULLS_FIRST:=True}
QM_SORT_BY_ANSWERED_COUNT=${QM_SORT_BY_ANSWERED_COUNT:=False}
QM_SORT_BY_WHEN_ANSWERED_NEWEST=${QM_SORT_BY_WHEN_ANSWERED_NEWEST:=False}
QM_SORT_BY_WHEN_ANSWERED_OLDEST=${QM_SORT_BY_WHEN_ANSWERED_OLDEST:=True}
QM_DEBUG_PRINT=${QM_DEBUG_PRINT:=False}
QM_DEBUG_SQL=${QM_DEBUG_SQL:=False}
QM_USE_TOOLBAR=${QM_USE_TOOLBAR:=False}

env | sort

set -eu;
set +vx
echo "+ $(poetry env info --path)/bin/activate"
source $(poetry env info --path)/bin/activate
set -vx; \

TIMEOUT_SECONDS_GUNICORN=120
time gunicorn \
        --bind 0.0.0.0:80 \
            --access-logfile - \
            --access-logformat '%(t)s|%(s)s|%(m)s|%(U)s|%(q)s|%(L)s|%(B)s|%(f)s' \
            --log-level info \
            --max-requests 100 \
            --max-requests-jitter 10 \
            --timeout $TIMEOUT_SECONDS_GUNICORN \
        quizme.wsgi; \
date
echo 'gunicorn exited'