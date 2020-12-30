import io
import os
from io import StringIO
from io import BytesIO
import tempfile

import numpy as np
from PIL import Image
from flask import Flask, request, send_file, jsonify, make_response, Response
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from anonymizer.anonymizer.detection.opencv_detector import OpenCVDetector

from anonymizer.anonymizer.anonymization.anonymizer import Anonymizer
from anonymizer.anonymizer.detection.detector import Detector
from anonymizer.anonymizer.detection.weights import get_weights_path
from anonymizer.anonymizer.obfuscation.obfuscator import Obfuscator

app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CORS_EXPOSE_HEADERS'] = ['filename']

# GLOBAL SETTINGS
PROCESS_FILES = True
STORE_FILES = False
WEIGHTS_PATH = 'weights'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

from anonymizer.anonymizer.detection.weights import download_weights

download_weights(WEIGHTS_PATH)

# set default values
obfuscation_params = '21,2,9'
kernel_size, sigma, box_kernel_size = obfuscation_params.split(',')

# create obfuscator and detectors
obfuscator = Obfuscator(kernel_size=int(kernel_size), sigma=float(sigma), box_kernel_size=int(box_kernel_size))
detectors = {
    # 'face': Detector(kind='face', weights_path=get_weights_path(WEIGHTS_PATH, kind='face')),
    'face': OpenCVDetector(),
    'plate': Detector(kind='plate', weights_path=get_weights_path(WEIGHTS_PATH, kind='plate'))
}

detection_thresholds = {
    'face': 0.3,
    'plate': 0.3
}

# build anonymizer
anonymizer = Anonymizer(obfuscator=obfuscator, detectors=detectors)



@app.route('/')
def hello_world():
    return 'Hello, World!'


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ext(filename:str) -> str:
    _, ext = os.path.splitext(filename)
    res = ext.replace(".", "")

    # edge cases i hate
    if res.lower() == 'jpg':
        res = 'jpeg'

    return  res

@app.route('/transform', methods=['POST'])
@cross_origin()
def transform():
    file = None
    path = ""

    # check if the request has sent us files
    if 'file' not in request.files:
        return "There was no file included", 500

    file = request.files['file']

    # check if name not empty and allowed
    if not (file and file.filename and allowed_file(file.filename)):
        return "The sent file was not correct", 500

    # store file, if asked
    if STORE_FILES:
        path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(path)
        file.seek(0)

    if PROCESS_FILES:
        LOAD_FROM_DISK = False
        # start processing
        if LOAD_FROM_DISK:
            res_image = Image.open('uploads/ANON_Screenshot_2020-12-12_at_00.36.23.png')
            # res_image.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename('AAANON_' + file.filename)))

        else:
            res_image = call_anonymizer_anonymize(file)
            res_image.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename('ANON_' + file.filename)))

        tmp = tempfile.TemporaryFile()
        res_image.save(tmp,format=get_ext(file.filename).lower())
        tmp.seek(0)
        resp = Response(tmp.read())
        # resp = Response(res_image, mimetype=file.mimetype, )


    else:

        # just send the file back
        resp = Response(file.read(), mimetype=file.mimetype)

    return resp


def call_anonymizer_anonymize(file):
    # get image from file -- critical
    file.seek(0)
    image = Image.open(file).convert('RGB')
    np_image = np.array(image)

    # anonymize using library
    image, _ = anonymizer.anonymize_image(image=np_image, detection_thresholds=detection_thresholds)

    # return image as RGB
    return Image.fromarray((image).astype(np.uint8), 'RGB')


@app.route('/transform_old', methods=['POST'])
@cross_origin()
def transform_old():
    file = None
    path = ""
    if request.method == 'POST':
        # check if the post request has the file part

        if 'file' not in request.files:
            print('No files in request')
            return "There were no files!-"
        file = request.files['file']

        if file.filename == '':
            return "no file was selected"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)

    anon = False
    if anon:
        conv_image = call_anonymizer_anonymize(file)
        resp = send_file(conv_image, mimetype=file.mimetype)
    else:
        resp = send_file(path, mimetype=file.mimetype)
        # resp = make_response(file.stream)
    file.seek(0)
    resp = Response(file.read(), mimetype=file.mimetype)
    return resp
