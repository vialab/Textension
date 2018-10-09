import sys
sys.path.append('./static/py')
import io
import os
from flask import Flask, request, redirect, url_for,send_from_directory,render_template,jsonify, send_file, session, jsonify
from werkzeug import secure_filename
import numpy as np
from PIL import Image
import base64
import re
import cStringIO
import imp
import pdf_text_extraction
import cPickle as pickle
import pickle_session as ps
import json
import wand.image as wi
from HTMLParser import HTMLParser
from input_text_processing import *

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = set(['bmp', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.session_interface = ps.PickleSessionInterface("./app_session")
h = HTMLParser()

default_options = {
    "spread":20,
    "hires":True,
    "cut":5,
    "noise":25,
    "buffer":1,
    "width":1024,
    "height":1024,
    "translate": False,
    "antialias": True,
    "blur":0,
    "google_key":""
}
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if "options" not in session:
        session["options"] = default_options
    return render_template('index2.html')

@app.route('/return_file')
def return_file():
    return send_file("./file_processing/ocr_document.pdf"
                    , attachment_filename="ocr_document.pdf")

@app.route('/interact')
@app.route('/interact/<page_no>')
def interact(page_no=0):
    """ Web hook that will load all the data processed from /upload """
    # samples are pre-processed and pickled for easy loading
    sample = request.args.get("sample")
    if sample is not None:
        if sample == "book_of_myths":
            sample = "./server/book_of_myths.pkl"
        if sample == "southern_life":
            sample = "./server/southern_life.pkl"
        with open(sample, 'r') as f:
            session["viz"] = pickle.load(f)
    # if we don't have a viz to render, redirect back home
    if "viz" not in session:
        return redirect(url_for("index"))
    # default to first page
    try:
        page_no = int(page_no)
    except:
        page_no = 0
    if page_no >= len(session["viz"]):
        page_no = 0

    # looping through the full arrays during rendering is slow due to size
    # segregate the data to matrices and do not include images
    image_text = formatToMatrix(session["viz"][page_no].img_text)
    image_patches = formatToMatrix(session["viz"][page_no].img_patches)
    image_patch_space = formatToMatrix(session["viz"][page_no].img_patch_space)
    image_space = formatToMatrix(session["viz"][page_no].img_space)

    return render_template('interact.html'
        , image_text=image_text
        , image_patches=image_patches
        , image_space=image_space
        , image_patch_space=image_patch_space
        , image_dim=session["viz"][page_no].chop_dimension
        , bounding_boxes=session["viz"][page_no].bounding_boxes
        , word_blocks=json.dumps(session["viz"][page_no].word_blocks)
        , ngram_plot=json.dumps(session["viz"][page_no].ngram_plot)
        , ocr=json.dumps([h.unescape(line) for line in session["viz"][page_no].ocr_text])
        , translation=json.dumps([h.unescape(line) for line in session["viz"][page_no].ocr_translated])
        , page_no=page_no
        , num_pages=len(session["viz"]))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """ Receive images from the dropzone and process it. Processed data is
     saved to the session and used later on for rendering in JINJA2 """
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            saveVizSessionArgs(request.form)
            file_extension = file.filename.split(".")[-1].lower()
            
            viz_list = []

            if file_extension == "pdf":
                # need to split pages and decompose one by one
                pdf_pages = pdfSplitPageStream(file.stream)
                for page in pdf_pages:
                    page.seek(0)
                    viz = iv.InlineViz(page, _translate=session["options"]["translate"]
                                , _vertical_spread=session["options"]["spread"]
                                , _hi_res=session["options"]["hires"]
                                , _anti_alias=session["options"]["antialias"]
                                , _pixel_cut_width=session["options"]["cut"]
                                , _noise_threshold=session["options"]["noise"]
                                , _line_buffer=session["options"]["buffer"]
                                , _blur=session["options"]["blur"]
                                , _google_key=session["options"]["google_key"]
                                , _max_size=(session["options"]["width"],session["options"]["height"]))
                    viz.decompose()
                    viz_list.append(viz)
            else:
                # just an image
                viz = iv.InlineViz(file.stream
                                , _translate=session["options"]["translate"]
                                , _hi_res=session["options"]["hires"]
                                , _anti_alias=session["options"]["antialias"]
                                , _vertical_spread=session["options"]["spread"]
                                , _pixel_cut_width=session["options"]["cut"]
                                , _noise_threshold=session["options"]["noise"]
                                , _line_buffer=session["options"]["buffer"]
                                , _blur=session["options"]["blur"]
                                , _google_key=session["options"]["google_key"]
                                , _max_size=(session["options"]["width"],session["options"]["height"]))
                viz.decompose()
                viz_list.append(viz)

            session["viz"] = viz_list
            # with open("./southern_life.pkl", "w+") as f:
            #     pickle.dump(viz_list, f)
    return redirect(url_for("index"))


@app.route('/hook', methods=['POST'])
def get_image():
    """ Retrieves image that was taken by the webcam, and processes like /upload """
    viz_list=[]
    saveVizSessionArgs(request.values)
    image_b64 = re.sub("data:image/png;base64,", "", request.values["imageBase64"])
    bImage = io.BytesIO(base64.b64decode(image_b64))
    img = Image.open(bImage)
    img = img.crop((133,5,499,img.size[1]-5))
    bImage = io.BytesIO()
    img.save(bImage, "PNG")
    img.save("test.png","PNG")    
    bImage.seek(0)
    viz = iv.InlineViz(bImage
                    , _translate=session["options"]["translate"]
                    , _hi_res=session["options"]["hires"]
                    , _anti_alias=session["options"]["antialias"]
                    , _vertical_spread=session["options"]["spread"]
                    , _pixel_cut_width=session["options"]["cut"]
                    , _noise_threshold=session["options"]["noise"]
                    , _line_buffer=session["options"]["buffer"]
                    , _blur=session["options"]["blur"]
                    , _google_key=session["options"]["google_key"]
                    , _max_size=(session["options"]["width"],session["options"]["height"]))
    viz.decompose()
    viz_list.append(viz)
    session["viz"] = viz_list
    return redirect(url_for("index"))



##### HELPER FUNCTIONS
def saveVizSessionArgs(form):
    """ Save visualization parameters into session"""
    if "options" not in session:
        session["options"] = default_options
        
    options_form = session["options"]

    for option in form:
        if option not in options_form:
            # don't save unnecessary data
            continue
        if option == "translate" or option == "hires" or option == "antialias":
            if form[option] == u"true":
                options_form[option] = True
            else:
                options_form[option] = False
            continue
        if option == "google_key":
            options_form[option] = form[option]
        else:
            options_form[option] = int(form[option])

    session["options"] = options_form


def allowed_file(filename):
    """ check if the uploaded file extension is allowed """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
       

def formatToMatrix(data):
    """ Itemize our data into dict multi-d arrays for consistency 
     and efficiency by filtering out the images """
    new_array = []
    for row in data:
        item = []
        for col in row:
            item.append(dict((i,col[i]) for i in col if i!="img"))
        new_array.append(item)
    return new_array

if __name__ == "__main__":
    sess.init_app(app)
    app.run(debug=True)