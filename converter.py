"""
GIS4Graph/converter.py
Developed by Aurelienne Jorge (aurelienne@gmail.com)
"""

import psycopg2
from igraph import *
#import matplotlib as mpl
#mpl.use('Agg')
#import matplotlib.pyplot as plt
import configparser
import os
import simplejson
import sys
from unicodedata import normalize
import zipfile
import subprocess
import datetime

config = configparser.ConfigParser()
py_path = os.path.dirname(os.path.abspath(__file__))
config.read_file(open(os.path.join(py_path,'defaults.cfg')))
hostDB = config.get('DB','host')
userDB = config.get('DB','user')
passDB = config.get('DB','pasw')
nameDB = config.get('DB','name')
portDB = config.get('DB','port')
SRID = config.get('DB','srid')

class Database:

    def __init__(self, file_in='', file_out='', pid='', data_type=''):
        self.conn = None
        self.file_in = file_in
        self.file_out = file_out
        self.data_type = data_type
        self.pid = str(pid)
        self.netwk_table = 'g4g_network_' + self.pid
        self.nodes_table = 'g4g_nodes_' + self.pid
        self.conex_table = 'g4g_relations_' + self.pid

        if file_in != '':
            self.create_database()
            # self.insert_pid()
            if data_type == '.shp':
                self.import_shapefile()
                self.alter_nodes_table()
                self.map_relations()
            elif data_type == '.osm':
                self.import_osm()
                self.map_nodes_osm()
                self.alter_nodes_table()
                self.map_relations_osm()
            else:
                print('ERRO: Extensão '+data_type+' nao suportada pela ferramenta!')
                sys.exit()
        else:
            self.conn = psycopg2.connect(
                "host=" + hostDB + " port=" + portDB + " dbname=" + nameDB + " user=" + userDB + " password=" + passDB)

    def create_database(self):
        os.environ['PGPASSWORD'] = passDB
        cont=subprocess.check_output('psql -lqt -h ' + hostDB + ' -U ' + userDB + ' -w | cut -d \| -f 1 | grep ' + nameDB + ' | wc -l', shell=True).decode('ascii').strip()
        if cont == '0':
            os.system('psql -h '+hostDB+' -p '+portDB+' -U '+userDB+' -w -c "create database '+nameDB+'"')
            conn = psycopg2.connect("host="+hostDB+" port="+portDB+" dbname="+nameDB+" user="+userDB+" password="+passDB)
            cur = conn.cursor()
            cur.execute('create extension postgis')
            conn.commit()
            cur.close()
            conn.close()
        self.conn = psycopg2.connect("host="+hostDB+" port="+portDB+" dbname="+nameDB+" user="+userDB+" password="+passDB)
        self.cria_tabela_geral()
        self.cria_tabela_conexoes()

    def import_shapefile(self):
        os.environ['PGPASSWORD'] = passDB
        os.system('shp2pgsql -s '+SRID+' -d -I -W "latin1" '+self.file_in+' public.'+self.nodes_table+' | psql -h '+hostDB+' -p '+portDB+' -d '+nameDB+' -U '+userDB+' -w')

    def alter_nodes_table(self):
        cur = self.conn.cursor()
        cur.execute('alter table '+self.nodes_table+' add column grau integer')
        cur.execute('alter table '+self.nodes_table+' add column grau_in integer')
        cur.execute('alter table '+self.nodes_table+' add column grau_out integer')
        cur.execute('alter table '+self.nodes_table+' add column coef_aglom numeric(6,2)')
        cur.execute('alter table '+self.nodes_table+' add column mencamed numeric(14,4)')
        cur.execute('alter table '+self.nodes_table+' add column betweeness numeric(14,6)')
        cur.execute('alter table '+self.nodes_table+' add column closeness numeric(6,4)')
        self.conn.commit()
        cur.close()

    def import_osm(self):
        os.system('osm2pgrouting --clean --file '+self.file_in+' --suffix _'+self.pid+' --dbname '+nameDB+' --username '+userDB)

    def map_nodes_osm(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists ' + self.nodes_table)
        self.conn.commit()

        cur.execute('create table '+self.nodes_table+' (gid bigserial, osm_id bigint, name text, ' +
                    'geom geometry(Multilinestring,4326), ' +
                    'CONSTRAINT '+self.nodes_table+'_pkey PRIMARY KEY (gid))')
        cur.execute('CREATE INDEX '+self.nodes_table+'_gdx ON '+self.nodes_table+
                    ' USING gist (geom);')

        self.conn.commit()

        cur.execute('insert into '+self.nodes_table+' (osm_id, name, geom) ' +
                         'select osm_id, name, st_multi(st_union(the_geom)) from ways_'+self.pid +
                         ' group by 1,2')
        self.conn.commit()
        cur.close()

    def map_relations(self):
        cur_de = self.conn.cursor()
        cur_para = self.conn.cursor()
        cur = self.conn.cursor()

        cur.execute('insert into '+self.conex_table+' (de,para) '+
                    'select a.gid, b.gid from g4g_nodes_002 a, g4g_nodes_002 b '+
                    'where st_intersects(a.geom, b.geom) and b.gid > a.gid')

        cur_de.close()
        cur_para.close()
        cur.close()

    def map_relations_osm(self):
        cur = self.conn.cursor()
        cur.execute('insert into '+self.conex_table + '  (de,para) ' +
                    'select distinct g1.gid, g2.gid \
                    from ways_002 w1, ways_002 w2, ' + self.nodes_table + ' as g1, ' + self.nodes_table + ' as g2 ' +
                    'where g1.osm_id = w1.osm_id \
                    and g2.osm_id = w2.osm_id \
                    and w1.osm_id <> w2.osm_id \
                    and w1.target = w2.source \
                    and w2.one_way = 1 \
                    UNION \
                    select distinct g1.gid, g2.gid \
                    from ways_002 w1, ways_002 w2, ' + self.nodes_table + ' as g1, ' + self.nodes_table + ' as g2 ' +
                    'where g1.osm_id = w1.osm_id \
                    and g2.osm_id = w2.osm_id \
                    and w1.osm_id <> w2.osm_id \
                    and (w1.target = w2.source or w1.target = w2.target) \
                    and w2.one_way <> 1')
        self.conn.commit()
        cur.close()

    def get_qtd_registros(self):
        cur = self.conn.cursor()
        cur.execute('select count(*) from '+self.nodes_table)
        qtd_registros = cur.fetchone()[0]
        cur.close()
        return qtd_registros

    def get_conexoes(self):
        lista_conexoes = []
        cur = self.conn.cursor()
        cur.execute('select de, para from '+self.conex_table+' inner join '+self.nodes_table+' on de = gid')
        for result in cur:
            de, para = result[0], result[1]
            lista_conexoes.append((de, para))
        cur.close()
        return lista_conexoes

    def cria_tabela_geral(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists '+self.netwk_table)
        self.conn.commit()

        cur.execute('create table '+self.netwk_table+' ( \
                     ordem smallint, \
                     comprimento smallint, \
                     grau_medio numeric(6,2), \
                     coef_aglom_medio numeric(6,2), \
                     diametro smallint, \
                     densidade numeric(6,4))')
        self.conn.commit()
        cur.execute('insert into '+self.netwk_table+' (ordem) values (0)')
        self.conn.commit()
        cur.close()

    def cria_tabela_conexoes(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists '+self.conex_table)
        self.conn.commit()

        cur.execute('create table '+self.conex_table+' ( \
                     id bigserial, \
                     de bigint, \
                     para bigint,'
                    'CONSTRAINT '+self.conex_table+'_pkey PRIMARY KEY (id))')
        self.conn.commit()
        cur.close()

    def update_ordem_comp_densidade(self, ordem, comp, dens):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set ordem = %s, comprimento = %s, densidade = %s', (ordem, comp, dens))
        self.conn.commit()
        cur.close()

    def update_grau_vertice(self, id, grau, grau_in=None, grau_out=None):
        cur = self.conn.cursor()
        if grau_in is not None and grau_out is not None:
            cur.execute('update ' + self.nodes_table + ' set grau = %s, grau_in = %s, grau_out = %s \
            where gid = %s', (grau, grau_in, grau_out, id))
        else:
            cur.execute('update '+self.nodes_table+' set grau = %s where gid = %s', (grau, id))
        cur.close()

    def update_grau_medio(self, grau_medio):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set grau_medio = %s', (grau_medio, ))
        self.conn.commit()
        cur.close()

    def update_coef_aglomeracao(self, id, coef):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set coef_aglom = %s where gid = %s', (coef, id))
        cur.close()

    def update_coef_aglom_medio(self, coef):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set coef_aglom_medio = %s', (coef, ))
        self.conn.commit()
        cur.close()

    def update_menor_caminho_medio(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set mencamed = %s where gid = %s', (valor, id))
        cur.close()

    def update_diametro(self, diametro):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set diametro = %s', (diametro,))
        self.conn.commit()
        cur.close()

    def update_betweeness(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set betweeness = %s where gid = %s', (valor, id))
        cur.close()

    def update_closeness(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set closeness = %s where gid = %s', (valor, id))
        cur.close()

    def encerra_conexao(self):
        self.conn.close()

    def export_shapefile(self):
       os.system('pgsql2shp -h '+hostDB+' -p '+portDB+' -u '+userDB+' -P '+passDB+' -f '+self.file_out+
                 ' '+nameDB+' "select * from '+self.nodes_table+', '+self.netwk_table+'"')

    def export_prop_json(self, gid, pid=''):
        if pid == '':
            pid = self.pid
        cur = self.conn.cursor()
        cols = ('gid', 'grau', 'grau_in', 'grau_out', 'coef_aglom', 'mencamed', 'betweeness', 'closeness')
        results = []
        cur.execute('select gid, grau, grau_in, grau_out, coef_aglom, mencamed, betweeness, closeness from '+self.nodes_table+
                    ' where gid = %s', (gid,))
        result = cur.fetchone()
        results.append(dict(zip(cols, result)))
        jsondata = simplejson.dumps(results, use_decimal=True)
        jsondata = jsondata.replace('[', '')
        jsondata = jsondata.replace(']', '').replace('NaN', '""')
        cur.close()
        return jsondata

    def export_geojson(self, where='', pid='', out=''):
        if pid == '':
            pid = self.pid
        cur = self.conn.cursor()
        cur.execute('select gid, st_asgeojson(geom) from '+self.nodes_table+' '+where+' order by gid')
        gjson = '{ "type": "FeatureCollection", "features": [ '
        for result in cur:
            gid = result[0]
            prop_json = self.export_prop_json(gid, pid)
            gjson = gjson+'{ "type": "Feature", "geometry": ' + result[1] + ', "properties": '+prop_json+'},'
        cur.close()
        gjson = gjson[0:-1] + ']}'
        if out == '':
            out = self.file_out
        gj = open(out+'.json','w')
        gj.write(gjson)
        gj.close()

    def export_grafojson(self):
        #Dict of nodes
        cur = self.conn.cursor()
        cur.execute('select gid, grau, grau_in, grau_out, coef_aglom, mencamed, betweeness, closeness from '+self.nodes_table+' order by gid')
        cols = ('gid', 'grau', 'grau_in', 'grau_out', 'coef_aglom', 'mencamed', 'betweeness', 'closeness')
        results = []
        for result in cur:
            results.append(dict(zip(cols, result)))
        cur.close()

        # Dict of edges
        cols = ('de','para')
        lista = []
        lista_conex = self.get_conexoes()
        for item in lista_conex:
            lista.append(dict(zip(cols, item)))

        # Puts together nodes and edges and dumps all as json
        grafodata = dict(labels=results, links=lista)
        jsondata = simplejson.dumps(grafodata, use_decimal=True)
        jsondata = jsondata.replace('NaN','""')
        jg = open(self.file_out + '_grafo.json', 'w')
        jg.write(jsondata)
        jg.close()


    def drop_tables(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists '+self.netwk_table)
        cur.execute('drop table if exists '+self.nodes_table)
        cur.execute('drop table if exists '+self.conex_table)
        self.conn.commit()


class Grafo:

    def __init__(self, qtd_vertices, lista_conexoes, fnameout, directed=False):
        self.ordem = qtd_vertices
        self.lista_conexoes = lista_conexoes
        self.comp = len(lista_conexoes)
        self.grafo = None
        self.fnameout = fnameout
        self.figura = os.path.join(fnameout+'_grafo.png')
        self.grau_medio = None
        self.coef_aglom_medio = None
        self.diametro = None
        self.betw_medio = None
        self.e_betw_medio = None
        self.closeness_medio = None
        self.directed = directed

        self.cria_grafo()
        #self.plota_grafo()
        self.densidade = self.grafo.density()

    def cria_grafo(self):
        self.grafo = Graph(directed=self.directed)
        self.grafo.add_vertices(self.ordem)
        for itens in self.lista_conexoes:
            de, para = itens[0], itens[1]
            self.grafo.add_edges([(de-1, para-1)])

    def plota_grafo(self):
        layout = self.grafo.layout("fr")
        visual_style = {}
        visual_style["vertex_size"] = 10
        plot(self.grafo, self.figura, layout=layout, bbox=(450, 300), **visual_style)

    def calcula_grau(self, db):
        grauList = self.grafo.degree()
        grauInList = self.grafo.degree(mode=IN)
        grauOutList = self.grafo.degree(mode=OUT)
        for i in range(self.grafo.vcount()):
            grau = grauList[i]
            grau_in = grauInList[i]
            grau_out = grauOutList[i]
            db.update_grau_vertice(i, grau, grau_in, grau_out)
        db.conn.commit()
        self.grau_medio = sum(self.grafo.degree()) / self.grafo.vcount()
        db.update_grau_medio(self.grau_medio)

    def calcula_coef(self, db):
        i = 0
        for coef in self.grafo.transitivity_local_undirected():
            i += 1
            db.update_coef_aglomeracao(i, coef)
        db.conn.commit()
        self.coef_aglom_medio = self.grafo.transitivity_avglocal_undirected(mode="zero")
        db.update_coef_aglom_medio(self.coef_aglom_medio)

    def menor_caminho_medio(self, db):
        for i in range(0, self.grafo.vcount()):
            mencam = self.grafo.shortest_paths_dijkstra(source=i)[0]
            caminhoMed = mean(mencam[x] for x in range(len(mencam)) if (mencam[x]!=float('Inf'))and(mencam[x]!=0))
            db.update_menor_caminho_medio(i+1, caminhoMed)
        db.conn.commit()
        diametro = self.grafo.diameter()
        db.update_diametro(diametro)
        self.diametro = diametro

    def plota_histograma(self):
        plt.hist(self.grafo.degree())
        plt.title("Histograma")
        plt.xlabel("Grau")
        plt.ylabel("Vertices")
        fig = plt.gcf()
        fig.set_size_inches(2.6, 2.2)
        fig.savefig(os.path.join(fnameout+'_hist.png'))

    def centralidade(self, db):
        lista_bet = self.grafo.betweenness()
        for i in range(0, len(lista_bet)):
            db.update_betweeness(i+1, lista_bet[i])
        db.conn.commit()
        lista_cls = self.grafo.closeness()
        for i in range(0, len(lista_cls)):
            db.update_closeness(i+1, lista_cls[i])
        db.conn.commit()


class Shp2Graph:

    def __init__(self, fnamein, fnameout, pid):
        print(datetime.datetime.now())
        file_type = os.path.splitext(fnamein)[-1]
        db = Database(fnamein, fnameout, pid, file_type)
        print("Import realizado - "+str(datetime.datetime.now()))
        qv = db.get_qtd_registros()
        lc = db.get_conexoes()
        if file_type == '.osm':  # Cria grafo direcionado
            self.grf = Grafo(qv, lc, fnameout, True)
        else:
            self.grf = Grafo(qv, lc, fnameout)
        print("Grafo construido - " + str(datetime.datetime.now()))
        db.update_ordem_comp_densidade(self.grf.ordem, self.grf.comp, self.grf.densidade)

        self.realiza_calculos(db)
        print("Calculos realizados - " + str(datetime.datetime.now()))
        #self.grf.plota_histograma()
        db.export_shapefile()
        db.export_geojson()
        db.export_grafojson()
        self.compress_files(fnameout)
        #db.drop_tables()
        db.encerra_conexao()

    def realiza_calculos(self, db):
        self.grf.calcula_grau(db)
        print("> Grau calculado - "+str(datetime.datetime.now()))
        self.grf.calcula_coef(db)
        print("> Coef. Aglom. calculado - "+str(datetime.datetime.now()))
        #self.grf.menor_caminho_medio(db)
        print("> Menor Caminho Médio calculado - "+str(datetime.datetime.now()))
        self.grf.centralidade(db)
        print("> Closeness e betweeness calculados - "+str(datetime.datetime.now()))

    def compress_files(self, fnameout):
        zipf = zipfile.ZipFile(fnameout+'.zip', 'w', zipfile.ZIP_DEFLATED)
        files = (fnameout+'.dbf', fnameout+'.shp', fnameout+'.shx', fnameout+'.prj', fnameout+'.txt', fnameout+'.json',
            fnameout+'_grafo.png', fnameout+'_hist.png')
        for item in files:
            if os.path.exists(item):
                zipf.write(item)
        zipf.close()

if __name__ == '__main__':
    if len(sys.argv) == 4:
        fnamein = sys.argv[1]
        fnameout = sys.argv[2]
        pid = sys.argv[3]
        Shp2Graph(fnamein, fnameout, pid)
    else:
        print('Informar path do arquivo de entrada, path de saida e id do processo!')
        sys.exit()
