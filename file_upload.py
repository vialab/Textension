import sys
sys.path.append('./static/py')
import io
import os
from flask import Flask, request, redirect, url_for,send_from_directory,render_template,jsonify, send_file, session
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
    "blur":0
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
           
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
    if "viz" not in session:
        return redirect(url_for("index"))

    image_blocks = []
    image_text = []
    image_patches = []

    for block in session["viz"][page_no].img_chops:
        image_block = []
        for chop in block:
            image_block.append(dict((i,chop[i]) for i in chop if i!="img"))
        image_blocks.append(image_block)
    
    for block in session["viz"][page_no].img_text:
        image_block = []
        for text in block:
            image_block.append(dict((i,text[i]) for i in text if i!="img"))
        image_text.append(image_block)

    for patch in session["viz"][page_no].img_patches:
        image_patches.append(dict((i,patch[i]) for i in patch if i!="img"))

    return render_template('interact.html', image_blocks=image_blocks
        , image_text=image_text
        , image_patches=image_patches
        , image_dim=session["viz"][page_no].chop_dimension
        , bounding_boxes=session["viz"][page_no].bounding_boxes
        , word_blocks=json.dumps(session["viz"][page_no].word_blocks)
        , ngram_plot=json.dumps(session["viz"][page_no].ngram_plot)
        , ocr=json.dumps([h.unescape(line) for line in session["viz"][page_no].ocr_text])
        , translation=json.dumps([h.unescape(line) for line in session["viz"][page_no].ocr_translated])
        , page_no=page_no)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    # with open('./viz.pkl', 'r') as f:
    #     session["viz"] = pickle.load(f)
    # return redirect(url_for("index"))

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
                                , _spread=session["options"]["spread"]
                                , _hi_res=session["options"]["hires"]
                                , _anti_alias=session["options"]["antialias"]
                                , _pixel_cut_width=session["options"]["cut"]
                                , _noise_threshold=session["options"]["noise"]
                                , _line_buffer=session["options"]["buffer"]
                                , _blur=session["options"]["blur"]
                                , _max_size=(session["options"]["width"],session["options"]["height"]))
                    viz.decompose()
                    viz_list.append(viz)
            else:
                # just an image
                viz = iv.InlineViz(file.stream
                                , _translate=session["options"]["translate"]
                                , _hi_res=session["options"]["hires"]
                                , _anti_alias=session["options"]["antialias"]
                                , _spread=session["options"]["spread"]
                                , _pixel_cut_width=session["options"]["cut"]
                                , _noise_threshold=session["options"]["noise"]
                                , _line_buffer=session["options"]["buffer"]
                                , _blur=session["options"]["blur"]
                                , _max_size=(session["options"]["width"],session["options"]["height"]))
                viz.decompose()
                viz_list.append(viz)

            session["viz"] = viz_list
            # with open("./vis.pkl", "w+") as f:
            #     pickle.dump(viz_list, f)
    return redirect(url_for("index"))

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
        options_form[option] = int(form[option])

    session["options"] = options_form

#This gets the camera image
@app.route('/hook', methods=['POST'])
def get_image():
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
                    , _spread=session["options"]["spread"]
                    , _pixel_cut_width=session["options"]["cut"]
                    , _noise_threshold=session["options"]["noise"]
                    , _line_buffer=session["options"]["buffer"]
                    , _blur=session["options"]["blur"]
                    , _max_size=(session["options"]["width"],session["options"]["height"]))
    viz.decompose()
    viz_list.append(viz)
    session["viz"] = viz_list
    return redirect(url_for("index"))

if __name__ == "__main__":
    sess.init_app(app)
    app.run(debug=True)