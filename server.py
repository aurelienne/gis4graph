from flask import Flask, send_from_directory, request, redirect
#from flask_restful import reqparse, abort, Api, Resource
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
        if secure_filename(f1.filename).split('.')[-1] != 'dbf':
            return redirect("/app/#/home/" + "Arquivo DBF incorreto. Informar novamente!", code=302)
        f1.save(dir+'/'+secure_filename(f1.filename))

        f2 = request.files['prj']
        if secure_filename(f2.filename).split('.')[-1] != 'prj':
            return redirect("/app/#/home/" + "Arquivo PRJ incorreto. Informar novamente!", code=302)
        f2.save(dir+'/'+secure_filename(f2.filename))

        f3 = request.files['shp']
        if secure_filename(f3.filename).split('.')[-1] != 'shp':
            return redirect("/app/#/home/" + "Arquivo SHP incorreto. Informar novamente!", code=302)
        f3.save(dir+'/'+secure_filename(f3.filename))

        f4 = request.files['shx']
        if secure_filename(f4.filename).split('.')[-1] != 'shx':
            return redirect("/app/#/home/" + "Arquivo SHX incorreto. Informar novamente!", code=302)
        f4.save(dir+'/'+secure_filename(f4.filename))

        return redirect("/converter/"+dir+'/'+secure_filename(f3.filename), code=302)

    if request.method == 'GET':
        return 'GET'


@app.route('/uploaderOSM', methods = ['GET', 'POST'])
def upload_file_osm():
    dir = 'in/'+str( uuid.uuid4())
    if request.method == 'POST':
        os.makedirs(dir)
        f1 = request.files['osm']
        if secure_filename(f1.filename).split('.')[-1] != 'osm':
            return redirect("/app/#/home/" + "Arquivo OSM incorreto. Informar novamente!", code=302)
        f1.save(dir+'/'+secure_filename(f1.filename))

        return redirect("/converter/"+dir+'/'+secure_filename(f1.filename), code=302)

    if request.method == 'GET':
        return 'GET'

@app.route('/converter/<path:path>', methods = ['GET', 'POST'])
def convert_shp2graph(path):
    pid = str(uuid.uuid4()).replace('-', '')
    if request.method == 'GET':
        os.makedirs('out/'+pid)
        import converter as c
        c.Shp2Graph(path, 'out/'+pid+'/out', pid)
        return redirect("/app/#/map/"+pid, code=302)


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
    pathjson = path
    fields = {'CA': 'coef_aglom', 'G':'grau', 'GI':'grau_in', 'GO':'grau_out', 'MC':'mencamed', 'C':'closeness',
              'B':'betweeness', 'ST':'straight', 'VU':'vulnerab'}
    if not os.path.exists(os.path.join('out', pathjson)):
        dir, file = os.path.split(pathjson)
        pid = dir
        filters = file.split('__')
        where = 'where '
        tag = ''
        for filter in filters[0:-1]:
            opts=filter.split('_')
            field = opts[0]
            start = opts[1][1:]
            end = opts[2][1:]
            field_name = fields.get(field)
            where = where+tag+field_name+' between '+str(start)+' and '+str(end)
            tag = ' and '
        print(where)

        import converter as c
        c.Database().export_geojson(where, pid, os.path.join('out', pathjson[0:-5]))

    return send_from_directory('out/', pathjson)

@app.route('/uid')
def uid():
    return str( uuid.uuid4())


if __name__ == '__main__':
    app.run(debug=True)
