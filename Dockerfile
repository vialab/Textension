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
        # python2.7-dev \
        python-pip \
        # python-tk \
        tesseract-ocr \
        # tesseract-ocr-all \
        # tesseract-ocr-eng \
        libtesseract-dev \
        libleptonica-dev \
        libmysqlclient-dev \ 
        libmagickwand-dev \
	poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip 
    #\
#    && pip install -r requirements.txt

# RUN pip install Werkzeug==0.14.1 flask==1.0.4 numpy scikit-learn==0.20 scipy==1.2.0 spacy pypdf2 pdfminer wand image google-api-python-client matplotlib==2.2.4 opencv-python pandas==0.24.2 pyocr==0.4.7 textstat tesserocr==2.4.1 imutils colour pdf2image uwsgi
# RUN pip install Werkzeug flask numpy scikit-learn==0.20 scipy==1.2.0 spacy pypdf2 pdfminer wand image google-api-python-client matplotlib==2.2.4 opencv-python pandas==0.24.2 pyocr textstat tesserocr==2.4.1 imutils colour pdf2image uwsgi
RUN pip install spacy==2.2.1

RUN python -m spacy download en
#pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz

RUN pip install -r requirements.txt

RUN rm -rf /usr/share/man

ENV FLASK_APP file_upload.py
EXPOSE 5000

COPY . /usr/src/app

CMD ["uwsgi", "uwsgi.ini"]
# CMD ["flask", "run", "--host=0.0.0.0"]

# This project is linked to an automated build on dockerhub