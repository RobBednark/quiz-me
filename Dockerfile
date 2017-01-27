# Base Image
FROM python:2.7
ENV PYTHONUNBUFFERED 1

# Add requirements.txt file to /opt/website directory
RUN mkdir /opt/website
ADD requirements.txt /opt/website
ADD requirements-debug.txt /opt/website
ADD requirements-test.txt /opt/website

# Install application dependencies
WORKDIR /opt/website
RUN virtualenv . && pip install -r requirements.txt -r requirements-debug.txt -r requirements-test.txt

# Install phantomjs for selenium browser testing
RUN apt-get update; \
    apt-get install -y \
    bison \
    build-essential \
    curl \
    flex \
    g++ \
    git \
    gperf \
    sqlite3 \
    libsqlite3-dev \
    fontconfig \
    libfontconfig1 \
    libfontconfig1-dev \
    libfreetype6 \
    libfreetype6-dev \
    libicu-dev \
    libjpeg-dev \
    libpng-dev \
    libssl-dev \
    libqt5webkit5-dev \
    ruby \
    perl \
    unzip \
    wget

RUN mkdir -p /usr/src; \
    cd /usr/src; \
    wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.0.0-source.zip; \
    unzip phantomjs-2.0.0-source.zip; \
    rm phantomjs-2.0.0-source.zip; \
    cd phantomjs-2.0.0; \
    ./build.sh --confirm

RUN cp /usr/src/phantomjs-2.0.0/bin/phantomjs /usr/local/bin/phantomjs
