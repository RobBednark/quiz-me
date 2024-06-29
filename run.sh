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