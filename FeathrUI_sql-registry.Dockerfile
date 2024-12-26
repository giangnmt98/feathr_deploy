# Stage 1: build frontend ui
FROM node:16-alpine AS ui-build
WORKDIR /usr/src/ui
COPY ./ui .

# Use api endpoint from same host and build production static bundle
RUN echo 'REACT_APP_API_ENDPOINT=' >> .env.production
RUN npm install && npm run build

# Stage 3: build the docker image for UI sandbox
FROM python:3.9.19-slim

USER root

RUN apt install tzdata -y
ENV TZ="Asia/Ho_Chi_Minh"

## Install dependencies
RUN apt-get update -y && apt-get install -y nginx freetds-dev sqlite3 libsqlite3-dev \
lsb-release gnupg lsof python3-dev default-libmysqlclient-dev build-essential pkg-config libpq-dev unixodbc-dev

# UI Section
## Remove default nginx index page and copy ui static bundle files
RUN rm -rf /usr/share/nginx/html/*
COPY --from=ui-build /usr/src/ui/build /usr/share/nginx/html
COPY ./deploy/nginx.conf /etc/nginx/nginx.conf

# Registry Section
# install registry
COPY ./registry /usr/src/registry
WORKDIR /usr/src/registry/sql-registry
RUN pip install -r requirements.txt

## Start service and then start nginx
WORKDIR /usr/src/registry
COPY ./feathr-sandbox/start_local_ui.sh /usr/src/registry/


USER root
WORKDIR /usr/src/registry
RUN ["chmod", "+x", "/usr/src/registry/start_local_ui.sh"]

# remove ^M chars in Linux to make sure the script can run
RUN sed -i "s/\r//g" /usr/src/registry/start_local_ui.sh


WORKDIR /home/jovyan/work
USER jovyan
ENV API_BASE="api/v1"
ENV FEATHR_SANDBOX=True

USER root

# RUN rm -rf /usr/src/registry/sql-registry
# 80: Feathr UI
EXPOSE 80