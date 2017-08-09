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
from input_text_processing import *

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = set(['bmp', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.session_interface = ps.PickleSessionInterface("./app_session")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
           
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index2.html')

@app.route('/return_file')
def return_file():
    return send_file("./file_processing/ocr_document.pdf"
                    , attachment_filename="ocr_document.pdf")

@app.route('/interact')
@app.route('/interact/<page_no>')
def interact(page_no=0):
    # with open('./vis.pkl', 'r') as f:
    #     session["vis"] = [pickle.load(f)]

    if "vis" not in session:
        return redirect(url_for("index"))

    image_blocks = []
    image_patches = []
    for block in session["vis"][page_no].img_blocks:
        bImage = io.BytesIO()
        block.save(bImage, format='PNG')
        image_blocks.append({ "src":bImage.getvalue().encode('base64')
                            , "width":block.size[0], "height":block.size[1] } )
        
    for strip in session["vis"][page_no].img_patches:
        bImage = io.BytesIO()
        strip.save(bImage, format='PNG')
        image_patches.append({ "src":bImage.getvalue().encode('base64')
        , "width":strip.size[0], "height":strip.size[1] } )

    return render_template('interact.html', image_blocks=image_blocks
        , word_blocks=json.dumps(session["vis"][page_no].word_blocks)
        , image_patches=image_patches
        , bounding_boxes=session["vis"][page_no].bounding_boxes)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    with open('./vis.pkl', 'r') as f:
        session["vis"] = [pickle.load(f)]
    return redirect(url_for("index"))    

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            file_extension = file.filename.split(".")[-1].lower()
            
            vis_list = []

            if file_extension == "pdf":
                # need to split pages and decompose one by one
                pdf_pages = pdfSplitPageStream(file.stream)
                for page in pdf_pages:
                    page.seek(0)
                    vis = iv.InlineViz(page, _translate=False, _spread=20)
                    vis.decompose()
                    vis_list.append(vis)
            else:
                # just an image
                vis = iv.InlineViz(file.stream, _translate=False, _spread=20)
                vis.decompose()
                vis_list.append(vis)

            session["vis"] = vis_list
    return redirect(url_for("index"))

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