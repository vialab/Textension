# Textension

The Textension platform automatically adds visualizations and natural language processing applications to analog texts, using any web-based device with a camera. After taking a picture of a particular page or set of pages from a book or uploading an existing image, our system builds an interactive digital object that automatically inserts modular elements in a digital space. Leveraging the findings of previous studies, our framework augments the reading of analog texts with digital tools, making it possible to work with texts in both a digital and analog environments.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This software was created in PYTHON 2.7 and is not compatible with more up to date versions.

A database connection is required for proper functioning of this software. Please create your own `dbconfig.py` file in the `./static/py/` directory. An example is provided:

```
mysql = {
    "host":"localhost",
    "port":2251,
    "user":"root",
    "passwd":"123456789",
    "db":"mydatabasename"
}
```

Along with this, you will also need to install some packages (UNIX):

```
apt-get update && apt-get install -y \
        build-essential \
        python-dev \
        python-pip \
        python-tk \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        libmagickwand-dev
```

### Installing

In order a local (non-containerized) version running on your machine, please run the provided commands (UNIX). 

Install and activate a Python 2.7 virtual environment (virtualenv):

```
cd /path/to/OpenSSH-Doc-Analyzer
virtualenv venv
source venv/bin/activate
```
Install Python dependencies:

```
pip install flask numpy scikit-learn scipy spacy pypdf2 pdfminer wand image \
google-api-python-client matplotlib opencv-python pandas pyocr textstat tesserocr

python -m spacy download en
```
Note: `pip install -r requirements.txt` might work as well (not tested)

### Running Flask

After successfully installing you should be able to run the Flask server with the following commands:

```
export FLASK_APP=file_upload.py
flask run
```

### Debugging

All development was done using [Visual Studio Code] (https://code.visualstudio.com/), and thus the `/.vscode` files have been provided in order for easy debugging of code. Simply, install the IDE, along with the Python package (in the IDE), select your debug options to Flask (note this is not the same as Flask (Old)) and press play.

The project should be available at the URL:
```
http://localhost:5000/
```

## Deployment

Deployment for this project has been automated, and so please be aware that pushes to this repository will automatically build, run, and deploy to the VIALAB production servers at https://textension.vialab.ca/. Deployment will automatically handle database connections through the injection of required environment variables in Kubernetes.

## Built With

* [Flask](http://flask.pocoo.org/) - The web framework used (PYTHON 2.7)
* [Jinja2](http://jinja.pocoo.org/docs/2.10/) - Template engine
* [Bootstrap](https://getbootstrap.com/) - Front-end component library
* [MySQL](https://www.mysql.com/) - Database back-end
* [Docker](https://www.docker.com/) - Container / Dependency management

## Versioning

This project is being developed using an iterative approach. Therefore, now releases have yet been made and the project will be subject to drastic changes. No versioning practices will be followed until release. To see a history of changes made to this project, see [commit history](https://github.com/vialab/OpenSSH-Doc-Analyzer/commits/).

## Authors

* Adam Bradley, PhD. - Research Associate
* Christopher Collins, PhD. - Research Supervisor
* Victor (Jay) Sawal, BSc. - Software Developer

## License

This research was conducted as part of the CO.SHS project (co-shs.ca) and has received financial support from the Canada Foundation for Innovation (Cyberinfrastructure Initiative – Challenge 1 – First competition).

## Acknowledgments

* Richard Drake, MSc. - Laboratory Technician (Science Building)
