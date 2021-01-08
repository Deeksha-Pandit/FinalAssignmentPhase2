# views.py

from flask import render_template, request, redirect, url_for, send_from_directory, flash, jsonify
import os
import urllib.request
from app import app
from zipfile import ZipFile 
import logging
import boto3
from botocore.exceptions import ClientError
from requests_toolbelt.multipart import decoder

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = '/tmp'

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/data/', methods = ['POST', 'GET'])
def data():
    if request.method == 'GET':
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == 'POST':
        form_data = request.form
        print("---------------------",form_data)
        user_name = request.form['UserName']
        print("###########",user_name)
        if(int(request.form['NumClasses']) > 1 and int(request.form['NumClasses']) <= 10):
        	if len(request.form['ClassNames'].split(',')) == int(request.form['NumClasses']):
        		return render_template('data.html',form_data = request.form['ClassNames'].split(','))
        	else:
        		return f"The classnames doesn't match number of classes. Try going back to submit form again"
        else:
        	return f"Number of classes must be atleast 2. Try going to back to submit form again"

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded files
    filenames = []
    resp=jsonify({'message' : 'None'})
    if 'files[]' not in request.files:
    	resp = jsonify({'message' : 'No file part in the request'})
    	resp.status_code = 400
    	return resp
    uploaded_files = request.files.getlist('files[]')
    class_name = request.form['className']
    print("-------------", uploaded_files)
    for file in uploaded_files:
        # Move the file form the temporal folder to the upload
        # folder we setup - after for loop upload to s3 (curl url)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        # Save the filename into a list, we'll use it later
        filenames.append(app.config["UPLOAD_FOLDER"]+"/"+file.filename)
        
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        #flash('succesfully uploaded')
    zip_file = app.config["UPLOAD_FOLDER"]+"/"+class_name+".zip" #/tmp/cat.zip
    with ZipFile(zip_file, 'w') as zip: 
        for file in filenames: 
            zip.write(file) 
         # extracting all the files 
        print('Zipping all the files now...') 
        print('Done!') 
    print("file names are:",filenames)
    upload_file(zip_file,"flaskdeployment", class_name, None)
    resp = jsonify({'message' : 'File Saved succesfully', 'files':filenames})
    return resp

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

def upload_file(file_name, bucket, class_name, object_name=None,):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    session = boto3.Session(
        aws_access_key_id='AKIAIP42E264TKZSBUDA',
        aws_secret_access_key='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',
        region_name='ap-south-1'
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket('flaskdeployment')

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, "flaskdeployment", class_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True                  