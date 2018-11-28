# Textension

A visualization tool built for researchers in the humanities and social sciences. 
This project aims to digitize physical pages/books into modular web objects that allow users to annotate, manipulate, and perform analytics.

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

Deployment is made simple due to the use of Docker. Before deploying in a live system, please contact the project authors in order to receive a copy of the database. 

Once a database connection can be made (locally), all that is left to do is to run the shell script using the command provided below, and ensure that the appropriate routing/proxies have been setup on your web server. 

NOTE: Modifications of used ports may be required.

```
./run.sh
```

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

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Richard Drake, MSc. - Laboratory Technician (Science Building)
