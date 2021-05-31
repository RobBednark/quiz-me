# 'pipenv shell' first to get in the virtualenv

# source this file (because don't want a subshell that isn't the virtualenv)
df -h .; \
DB_QUIZME=quizme_production \
make \
    DB_NAME_TO_DUMP=quizme_production \
    DB_PASSWORD=p \
    DB_SERVER=localhost \
    DB_USER=postgres \
    dumpdb
