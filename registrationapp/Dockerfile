# syntax=docker/dockerfile:1
FROM python:3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/home/app/registrationapp
# create directory for the app user
WORKDIR ${APP_HOME}
# create the app user
RUN adduser --system --group app
COPY requirements.txt ${APP_HOME}
RUN pip install -r requirements.txt
# copy project
COPY . ${APP_HOME}
# chown all the files to the app user
RUN chown -R app:app ${APP_HOME}
# change to the app user
USER app