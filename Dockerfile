FROM ubuntu:18.04

RUN sed -i 's/archive.ubuntu.com/mirror.science.uoit.ca/g' \
        /etc/apt/sources.list

ENV TZ=America/Toronto
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/app/requirements.txt

RUN apt-get update && apt-get install -y \
        build-essential \
        python2.7 \
        python-pip \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        libmagickwand-dev \
	    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip 

RUN pip install spacy==2.2.1

RUN python -m spacy download en
#pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz

RUN pip install -r requirements.txt

RUN rm -rf /usr/share/man \
    && apt-get remove -y \
        build-essential \
        gcc-7 \ 
        libtesseract-dev \
        libleptonica-dev \
    && apt-get autoremove -y --purge && apt-get autoclean -y && apt-get purge



COPY . /usr/src/app

EXPOSE 5000

ENV FLASK_APP file_upload.py
ENV FLASK_ENV production
ENV FLASK_DEBUG False

CMD ["uwsgi", "uwsgi.ini"]

# This project is linked to an automated build on dockerhub