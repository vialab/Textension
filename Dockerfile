FROM ubuntu:16.04

RUN sed -i 's/archive.ubuntu.com/mirror.science.uoit.ca/g' \
        /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
        build-essential \
        python-dev \
        python-pip \
        python-tk \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        libmagickwand-dev \
	poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip

RUN pip install flask numpy scikit-learn scipy spacy pypdf2 pdfminer wand image google-api-python-client matplotlib opencv-python pandas pyocr textstat tesserocr imutils

RUN python -m spacy download en
#pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz

ENV FLASK_APP file_upload.py

WORKDIR /usr/src/app

COPY . /usr/src/app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]

# This project is linked to an automated build on dockerhub
