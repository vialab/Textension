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
    "cut":5,
    "noise":25,
    "buffer":1,
    "width":1024,
    "height":1024,
    "translate": False
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
    # with open('./viz.pkl', 'r') as f:
    #     session["viz"] = [pickle.load(f)]

    if "viz" not in session:
        return redirect(url_for("index"))

    image_blocks = []
    image_text = []
    image_dim = []
    image_patches = []

    for idx, block in enumerate(session["viz"][page_no].img_chops):
        image_chops = []
        for chop in block:
            bImage = io.BytesIO()
            chop.save(bImage, format="PNG")
            image_chops.append({ "src":bImage.getvalue().encode('base64')
                            , "width":chop.size[0], "height":chop.size[1] })
        
        full_width, full_height = session["viz"][page_no].img_blocks[idx].size
        image_dim.append({"width":full_width, "height":full_height})
        image_blocks.append(image_chops)
    
    for idx, chop in enumerate(session["viz"][page_no].img_text):
        image_chops = []
        for word in chop:
            bImage = io.BytesIO()
            word.save(bImage, format="PNG")
            image_chops.append({ "src":bImage.getvalue().encode('base64')
                            , "width":word.size[0]
                            , "height":word.size[1] })
        image_text.append(image_chops)

    # for block in session["viz"][page_no].img_blocks:
    #     bImage = io.BytesIO()
    #     block.save(bImage, format='PNG')
    #     image_blocks.append({ "src":bImage.getvalue().encode('base64')
    #                         , "width":block.size[0], "height":block.size[1] } )
        
    for strip in session["viz"][page_no].img_patches:
        bImage = io.BytesIO()
        strip.save(bImage, format='PNG')
        image_patches.append({ "src":bImage.getvalue().encode('base64')
        , "width":strip.size[0], "height":strip.size[1] } )

    return render_template('interact.html', image_blocks=image_blocks
        , image_text=image_text
        , image_dim=image_dim
        , word_blocks=json.dumps(session["viz"][page_no].word_blocks)
        , image_patches=image_patches
        , bounding_boxes=session["viz"][page_no].bounding_boxes
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
                                , _pixel_cut_width=session["options"]["cut"]
                                , _noise_threshold=session["options"]["noise"]
                                , _line_buffer=session["options"]["buffer"]
                                , _max_size=(session["options"]["width"],session["options"]["height"]))
                    viz.decompose()
                    viz_list.append(viz)
            else:
                # just an image
                viz = iv.InlineViz(file.stream
                                , _translate=session["options"]["translate"]
                                , _spread=session["options"]["spread"]
                                , _pixel_cut_width=session["options"]["cut"]
                                , _noise_threshold=session["options"]["noise"]
                                , _line_buffer=session["options"]["buffer"]
                                , _max_size=(session["options"]["width"],session["options"]["height"]))
                viz.decompose()
                viz_list.append(viz)

            session["viz"] = viz_list
            with open("./vis.pkl", "w+") as f:
                pickle.dump(viz_list, f)
    return redirect(url_for("index"))

def saveVizSessionArgs(form):
    """ Save visualization parameters into session"""
    if "options" not in session:
        session["options"] = default_options
    
    for option in form:
        if option not in session["options"]:
            # don't save unnecessary data
            continue
        if option == "translate":
            if form[option] == u"true":
                session["options"][option] = True
            else:
                session["options"][option] = False

        session["options"][option] = form[option]

#This gets the camera image
@app.route('/hook', methods=['POST'])

def get_image():
    image_b64 = request.values['imageBase64']
    image_data = re.sub('^data:image/.+;base64,', '', image_b64).decode('base64')
    image_PIL = Image.open(cStringIO.StringIO(image_data))
    image_np = np.array(image_PIL)
    im = Image.fromarray(image_np)
    im.save(os.path.join(app.config['UPLOAD_FOLDER'],'test.png'))

    for filename in os.listdir('./uploads/'):
        if not filename3.startswith('.'):
            findBoundingBoxes('./uploads/'+filename)

    #print 'Image received: {}'.format(image_np.shape)
    #return ''



if __name__ == "__main__":
    sess.init_app(app)
    app.run(debug=True)