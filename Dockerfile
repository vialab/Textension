# FROM ubuntu:18.04
FROM python:3

# RUN sed -i 's/archive.ubuntu.com/mirror.science.uoit.ca/g' \
#         /etc/apt/sources.list

ENV TZ=America/Toronto
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
        build-essential \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        pkg-config
#         python2.7 \
#         python-pip \
#         libtesseract-dev \
#         libleptonica-dev \
#         libmagickwand-dev \
# 	    poppler-utils \
#     && rm -rf /var/lib/apt/lists/* \
#     && python -m pip install --upgrade pip 

# RUN pip install spacy==2.2.1

#pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz

WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt
RUN python -m spacy download en

# RUN rm -rf /usr/share/man \
#     && apt-get remove -y \
#         build-essential \
#         gcc-7 \ 
#         libtesseract-dev \
#         libleptonica-dev \
#     && apt-get autoremove -y --purge && apt-get autoclean -y && apt-get purge

RUN pip install textstat


COPY . /usr/src/app

EXPOSE 5000

ENV LC_ALL=C 

ENV FLASK_APP file_upload.py
ENV FLASK_ENV production
ENV FLASK_DEBUG False

# CMD ["uwsgi", "uwsgi.ini"]
CMD ["flask", "run", "-h" ,"0.0.0.0"]

# This project is linked to an automated build on dockerhub