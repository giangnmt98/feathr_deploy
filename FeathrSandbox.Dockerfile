# Stage 1: build frontend ui
FROM node:16-alpine AS ui-build
WORKDIR /usr/src/ui
COPY ./ui .

# Use api endpoint from same host and build production static bundle
RUN echo 'REACT_APP_API_ENDPOINT=' >> .env.production
RUN npm install && npm run build

# Stage 2: build feathr runtime jar
# FROM gradle:7.6.0-jdk8 AS gradle-build
# WORKDIR /usr/src/feathr
# COPY . .
# RUN ./gradlew build

# Stage 3: build the docker image for feathr sandbox
FROM jupyter/pyspark-notebook:python-3.9.12

USER root

RUN apt install tzdata -y
ENV TZ="Asia/Ho_Chi_Minh"

## Install dependencies
RUN apt-get update -y && apt-get install -y nginx freetds-dev sqlite3 libsqlite3-dev \
lsb-release redis gnupg redis-server lsof python3-dev default-libmysqlclient-dev build-essential pkg-config libpq-dev unixodbc-dev

# UI Section
## Remove default nginx index page and copy ui static bundle files
RUN rm -rf /usr/share/nginx/html/*
COPY --from=ui-build /usr/src/ui/build /usr/share/nginx/html
COPY ./deploy/nginx.conf /etc/nginx/nginx.conf

# Feathr Package Installation Section
# always install feathr from main
WORKDIR /home/jovyan/work
COPY --chown=1000:100 ./feathr_project ./feathr_project

RUN python -m pip install -e ./feathr_project

# Registry Section
# install registry
COPY ./registry /usr/src/registry
WORKDIR /usr/src/registry/sql-registry
RUN pip install -r requirements.txt

## Start service and then start nginx
WORKDIR /usr/src/registry
COPY ./feathr-sandbox/start_local.sh /usr/src/registry/

# default dir by the jupyter image
WORKDIR /home/jovyan/work
USER jovyan
#COPY --chown=1000:100 ./feathr-sandbox/feathr_init_script.py .
COPY --chown=1000:100 ./docs/samples ./samples

RUN python -m pip install --user interpret==0.2.7

# USER root
# COPY --chown=1000:100 ./.ivy2 /home/jovyan/.ivy2

USER root
WORKDIR /usr/src/registry
RUN ["chmod", "+x", "/usr/src/registry/start_local.sh"]

# remove ^M chars in Linux to make sure the script can run
RUN sed -i "s/\r//g" /usr/src/registry/start_local.sh

# install a Kafka single node instance
# Reference: https://www.looklinux.com/how-to-install-apache-kafka-single-node-on-ubuntu/
RUN wget https://downloads.apache.org/kafka/3.8.0/kafka_2.12-3.8.0.tgz && tar xzf kafka_2.12-3.8.0.tgz && mv kafka_2.12-3.8.0 /usr/local/kafka && rm kafka_2.12-3.8.0.tgz

WORKDIR /home/jovyan/work
USER jovyan
ENV API_BASE="api/v1"
ENV FEATHR_SANDBOX=True
# keep update cache!!
#RUN /usr/src/registry/start_local.sh -m build_docker && python feathr_init_script.py

USER root

RUN rm -rf /usr/src/registry/sql-registry
#RUN rm /home/jovyan/work/*jar

# 80: Feathr UI
# 8888: Jupyter
# 7080: Interpret
EXPOSE 80 8888 7080 2181
