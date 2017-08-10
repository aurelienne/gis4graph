from flask import Flask, send_from_directory, request, redirect
from flask_restful import reqparse, abort, Api, Resource
from werkzeug import secure_filename
import uuid
import os

app = Flask(__name__)


@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    dir = 'in/'+str( uuid.uuid4())
    if request.method == 'POST':
        os.makedirs(dir)
        f1 = request.files['dbf']
        f1.save(dir+'/'+secure_filename(f1.filename))
        f2 = request.files['prj']
        f2.save(dir+'/'+secure_filename(f2.filename))
        f3 = request.files['shp']
        f3.save(dir+'/'+secure_filename(f3.filename))
        f4 = request.files['shx']
        f4.save(dir+'/'+secure_filename(f4.filename))
        return redirect("/converter/"+dir+'/'+secure_filename(f3.filename), code=302)
    if request.method == 'GET':
        return 'GET'


@app.route('/converter/<path:path>', methods = ['GET', 'POST'])
def convert_shp2graph(path):
    dir = str( uuid.uuid4())
    if request.method == 'GET':
        os.makedirs('out/'+dir)
        import converter as c
        c.Shp2Graph(path, 'out/'+dir+'/out')
        return redirect("/app/#/map/"+dir, code=302)


@app.route('/app')
def send_app_root():
    return send_from_directory('app', 'index.html')

@app.route('/app/')
def send_app_root_bar():
    return send_from_directory('app', 'index.html')

@app.route('/app/<path:path>')
def send_app(path):
    return send_from_directory('app/', path)


@app.route('/out/<path:path>')
def send_out(path):
    return send_from_directory('out/', path)

@app.route('/uid')
def uid():
    return str( uuid.uuid4())


if __name__ == '__main__':
    app.run(debug=True)
