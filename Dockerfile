# Base Image
FROM python:2.7
ENV PYTHONUNBUFFERED 1

# Add requirements.txt file to /opt/website directory
RUN mkdir /opt/website
ADD requirements.txt /opt/website

# Install application dependencies
WORKDIR /opt/website
RUN virtualenv . && pip install -r requirements.txt
