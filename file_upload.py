import sys
sys.path.append('./static/py')
import io
import os
from flask import Flask, request, redirect, url_for,send_from_directory,render_template,jsonify, send_file
from werkzeug import secure_filename
import numpy as np
from PIL import Image
import base64
import re
import cStringIO
import imp
import pdf_text_extraction
import cPickle as pickle
from input_text_processing import *

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = set(['docx','txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
           
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index2.html')

@app.route('/return_file')
def return_file():
    return send_file('./file_processing/ocr_document.pdf', attachment_filename="ocr_document.pdf")

@app.route('/interact')
def interact():
    with open('./vis.pkl', 'r') as f:
        vis = pickle.load(f)

    image_blocks = []
    image_patches = []
    for block, strip in zip(vis.img_blocks, vis.img_patches):
        bImage = io.BytesIO()
        block.save(bImage, format='PNG')
        image_blocks.append(bImage.getvalue().encode('base64'))
        bImage = io.BytesIO()        
        strip.save(bImage, format='PNG')
        image_patches.append(bImage.getvalue().encode('base64'))

    return render_template('interact.html', image_blocks=image_blocks, image_patches=image_patches)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            textProcessing(filename)

    return "ooooooppppppssss"

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