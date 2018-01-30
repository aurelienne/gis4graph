"""
GIS4Graph/converter.py
Developed by Aurelienne Jorge (aurelienne@gmail.com)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
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
#from concurrent.futures import as_completed, ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mproc

config = configparser.ConfigParser()
py_path = os.path.dirname(os.path.abspath(__file__))
config.read_file(open(os.path.join(py_path,'defaults.cfg')))
hostDB = config.get('DB','host')
userDB = config.get('DB','user')
passDB = config.get('DB','pasw')
nameDB = config.get('DB','name')
portDB = config.get('DB','port')
SRID = config.get('FILE','srid')

class Database:

    def __init__(self, file_in='', file_out='', pid='', data_type='', options=''):
        self.conn = None
        self.file_in = file_in
        self.file_out = file_out
        self.data_type = data_type
        self.pid = str(pid)
        self.netwk_table = 'g4g_network_' + self.pid
        self.nodes_table = 'g4g_nodes_' + self.pid
        self.conex_table = 'g4g_relations_' + self.pid
        self.ways_table = 'ways_' + self.pid
        self.cols = None
        self.degree_enabled = False
        self.clustcoeff_enabled = False
        self.shortpath_enabled = False
        self.betweeness_enabled = False
        self.closeness_enabled = False
        self.straight_enabled = False
        self.vulnerab_enabled = False
        self.strahler_enabled = False

        if options[0] == 'S':
            self.degree_enabled = True
        if options[1] == 'S':
            self.clustcoeff_enabled = True
        if options[2] == 'S':
            self.shortpath_enabled = True
        if options[3] == 'S':
            self.betweeness_enabled = True
        if options[4] == 'S':
            self.closeness_enabled= True
        if options[5] == 'S':
            self.straight_enabled = True
        if options[6] == 'S':
            self.vulnerab_enabled = True
        if options[7] == 'S':
            self.strahler_enabled = True

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

    def create_connection(self):
        conn = psycopg2.connect(
                "host=" + hostDB + " port=" + portDB + " dbname=" + nameDB + " user=" + userDB + " password=" + passDB)
        return conn

    def create_database(self):
        os.environ['PGPASSWORD'] = passDB
        cont=subprocess.check_output('psql -lqt -h ' + hostDB + ' -U ' + userDB + ' -w | cut -d \| -f 1 | grep ' + nameDB + ' | wc -l', shell=True).decode('ascii').strip()
        if cont == '0':
            os.system('psql -h '+hostDB+' -p '+portDB+' -U '+userDB+' -w -c "create database '+nameDB+'"')
            conn = psycopg2.connect("host="+hostDB+" port="+portDB+" dbname="+nameDB+" user="+userDB+" password="+passDB)
            cur = conn.cursor()
            cur.execute('create extension postgis; create extension pgrouting;')
            conn.commit()
            cur.close()
            conn.close()
        self.conn = psycopg2.connect("host="+hostDB+" port="+portDB+" dbname="+nameDB+" user="+userDB+" password="+passDB)
        self.create_netwk_table()
        self.create_conex_table()

    def import_shapefile(self):
        os.environ['PGPASSWORD'] = passDB
        os.system('shp2pgsql -s '+SRID+' -d -I -W "latin1" '+self.file_in+' public.'+self.nodes_table+' | psql -h '+hostDB+' -p '+portDB+' -d '+nameDB+' -U '+userDB+' -w')
        #os.system('shp2pgsql -s ' + SRID + ' -d -I ' + self.file_in + ' public.' + self.nodes_table + ' | psql -h ' + hostDB + ' -p ' + portDB + ' -d ' + nameDB + ' -U ' + userDB + ' -w')

    def alter_nodes_table(self):
        cur = self.conn.cursor()
        if self.degree_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column grau integer')
            cur.execute('alter table ' + self.nodes_table + ' add column grau_in integer')
            cur.execute('alter table ' + self.nodes_table + ' add column grau_out integer')
        if self.clustcoeff_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column coef_aglom numeric(6,2)')
        if self.shortpath_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column mencamed numeric(14,4)')
        if self.betweeness_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column betweeness numeric(14,6)')
        if self.closeness_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column closeness numeric(6,4)')
        if self.vulnerab_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column vulnerab numeric(8,6)')
        if self.straight_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column straight numeric(8,6)')
        if self.strahler_enabled == True:
            cur.execute('alter table ' + self.nodes_table + ' add column flow integer')
            cur.execute('alter table ' + self.nodes_table + ' add column _strahler integer')
            cur.execute('create index ix_'+self.nodes_table+'_strahler on '+self.nodes_table+ ' using btree(_strahler)')
            cur.execute('create index ix_'+self.nodes_table+'_flow on '+self.nodes_table+ ' using btree(flow)')

        self.conn.commit()
        cur.close()

    def import_osm(self):
        os.system('osm2pgrouting --clean --file '+self.file_in+' --suffix _'+self.pid+' --dbname '+nameDB+' --username '+userDB)

    def map_nodes_osm(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists ' + self.nodes_table)
        self.conn.commit()

        cur.execute("select pgr_createTopology('"+self.ways_table+"', 0.0001, 'the_geom', 'gid', 'source', 'target')")
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
                    'select a.gid, b.gid from '+self.nodes_table+' a, '+self.nodes_table+' b '+
                    'where st_intersects(a.geom, b.geom) and b.gid > a.gid')

        cur_de.close()
        cur_para.close()
        cur.close()

    def map_relations_osm(self):
        cur = self.conn.cursor()
        cur.execute('insert into '+self.conex_table + '  (de,para) ' +
                    'select distinct g1.gid, g2.gid \
                    from ways_'+self.pid+' w1, ways_'+self.pid+' w2, ' + self.nodes_table + ' as g1, ' + self.nodes_table + ' as g2 ' +
                    'where g1.osm_id = w1.osm_id \
                    and g2.osm_id = w2.osm_id \
                    and w1.osm_id <> w2.osm_id \
                    and w1.target_osm = w2.source_osm \
                    and w2.one_way = 1 \
                    UNION \
                    select distinct g1.gid, g2.gid \
                    from ways_'+self.pid+' w1, ways_'+self.pid+' w2, ' + self.nodes_table + ' as g1, ' + self.nodes_table + ' as g2 ' +
                    'where g1.osm_id = w1.osm_id \
                    and g2.osm_id = w2.osm_id \
                    and w1.osm_id <> w2.osm_id \
                    and (w1.target_osm = w2.source_osm or w1.target_osm = w2.target_osm) \
                    and w2.one_way <> 1')
        self.conn.commit()
        cur.close()

    def get_qtd_registros(self):
        cur = self.conn.cursor()
        cur.execute('select count(*) from '+self.nodes_table)
        qtd_registros = cur.fetchone()[0]
        cur.close()
        return qtd_registros

    def get_conex(self):
        lista_conexoes = []
        cur = self.conn.cursor()
        cur.execute('select de, para from '+self.conex_table+' inner join '+self.nodes_table+' on de = gid')
        for result in cur:
            de, para = result[0], result[1]
            lista_conexoes.append((de, para))
        cur.close()
        return lista_conexoes

    def get_distance(self, source, targets):
        conn = self.create_connection()
        cur = conn.cursor()
        dists = []
        for target in targets:
            cur.execute('select st_distance(st_transform(g1.geom,5880),st_transform(g2.geom,5880))/1000 '
                        'from '+self.nodes_table+' as g1,'+
                                self.nodes_table+' as g2 '
                        'where g1.gid = %s and g2.gid = %s', (source, target))
            dists.append(float(cur.fetchone()[0]))
        cur.close()
        conn.close()
        return dists

    def get_min_route_path(self, i, j):
        conn = self.create_connection()
        cur = conn.cursor()
        cur.execute("select min(agg_cost) "+
                    "from pgr_dijkstra( "+
                    "'SELECT gid as id, source, target, length_m as cost "+
                    "FROM "+self.ways_table+"', "+
                    #Array of vertices inside source street
                    "ARRAY(select distinct id from "+
                    "(select source as id "+
                    "from "+self.nodes_table+" n, "+self.ways_table+" w "+
                    "where n.osm_id = w.osm_id "+
                    "and n.gid = %s "+
                    "UNION "+
                    "select target as id "+
                    "from "+self.nodes_table+" n, "+self.ways_table+" w "+
                    "where n.osm_id = w.osm_id "+
                    "and n.gid = %s) as sel), "+
                    # Array of vertices inside source street
                    "ARRAY(select distinct id from "+
                    "(select source as id "+
                    "from "+self.nodes_table+" n, "+self.ways_table+" w "+
                    "where n.osm_id = w.osm_id "+
                    "and n.gid = %s "+
                    "UNION "+
                    "select target as id "+
                    "from "+self.nodes_table+" n, "+self.ways_table+" w "+
                    "where n.osm_id = w.osm_id "+
                    "and n.gid = %s) as sel), "+
                    " true) "+
                    "where edge = -1", (i,i,j,j))
        path_len_mt = cur.fetchone()[0]
        cur.close()
        conn.close()
        return path_len_mt

    def create_netwk_table(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists '+self.netwk_table)
        self.conn.commit()

        cur.execute('create table '+self.netwk_table+' ( \
                     ordem smallint, \
                     comprimento smallint, \
                     grau_medio numeric(6,2), \
                     coef_aglom_medio numeric(6,2), \
                     diametro smallint, \
                     densidade numeric(6,4), \
                     strt_medio numeric(6,4))')
        self.conn.commit()
        cur.execute('insert into '+self.netwk_table+' (ordem) values (0)')
        self.conn.commit()
        cur.close()

    def create_conex_table(self):
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

    def update_avg_degree(self, grau_medio):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set grau_medio = %s', (grau_medio, ))
        self.conn.commit()
        cur.close()

    def update_clustering_coeff(self, id, coef):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set coef_aglom = %s where gid = %s', (coef, id))
        cur.close()

    def update_avg_cluster_coeff(self, coef):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set coef_aglom_medio = %s', (coef, ))
        self.conn.commit()
        cur.close()

    def update_avg_shortest_path(self, id, valor):
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

    def update_vulnerabilide(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set vulnerab = %s where gid = %s', (valor, id))
        cur.close()

    def update_straightness(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set straight = %s where gid = %s', (valor, id))
        cur.close()

    def update_avg_straight(self, valor):
        cur = self.conn.cursor()
        cur.execute('update '+self.netwk_table+' set strt_medio = %s', (valor,))
        cur.close()

    def flow_identifier(self, stream_field, mouth):
        cur = self.conn.cursor()
        cur2 = self.conn.cursor()
        cur.execute(
            'select b.'+stream_field+' from ' + self.nodes_table + ' a, ' + self.nodes_table + ' b where a.'
            +stream_field+' = %s and st_touches(a.geom, b.geom) and b.'+stream_field+' <> a.'+stream_field+
            ' and b.flow is null;',
            (mouth,))
        for result in cur:
            cur2.execute('update ' + self.nodes_table + ' set flow = %s where '+stream_field+' = %s;',
                         (mouth, result[0]))
            self.conn.commit()
            self.flow_identifier(stream_field, result[0])

    def strahler(self, stream_field, mouth):
        cur = self.conn.cursor()
        cur2 = self.conn.cursor()
        cur.execute('update '+self.nodes_table+' set flow = 0 where '+stream_field+' = %s', (mouth,))
        self.conn.commit()
        # Identify flow
        self.flow_identifier(stream_field, mouth)

        # Identify sources
        cur.execute('update '+self.nodes_table+' set _strahler = 1 where _strahler is null and '+stream_field+' in (select h1.'+stream_field+' from '+self.nodes_table+' h1 where h1.flow is not null and h1.cotrecho not in (select h2.flow from '+self.nodes_table+' h2 where h2.flow is not null))')

        # Classification
        i = 1
        while True:
            last = None
            cur.execute('select count(*) from '+self.nodes_table+' where _strahler is null and (flow is not null or '+
                        stream_field+' = %s);', (mouth,))
            count = (cur.fetchone())[0]
            if count == 0:
                break
            cur.execute('select flow, _strahler, count(*) as cont from '+self.nodes_table+' h1 '
                        'where h1._strahler is not null and h1.flow not in '
                            '(select h2.flow from '+self.nodes_table+' h2 where h2._strahler is null and h2.flow is not null) '
                        'and flow not in '
                            '(select h3.'+stream_field+' from '+self.nodes_table+' h3 where h3._strahler is not null) '
                        'and flow is not null and flow <> 0 group by 1,2 order by 1 asc, 2 desc;')
            for reslast in cur:
                stream = reslast[0]
                strahler = reslast[1]
                count = reslast[2]
                print(stream, strahler, count)

                # print "Cotrecho = "+str(cotrecho)
                if stream != last:
                    if count == 1:
                        cur2.execute('update '+self.nodes_table+' set _strahler = %s where '+stream_field+' = %s;',
                                     (strahler, stream))
                    else:
                        cur2.execute('update '+self.nodes_table+' set _strahler = %s where '+stream_field+' = %s;',
                                     (strahler + 1, stream))
                    last = stream

                    self.conn.commit()

    def encerra_conexao(self):
        self.conn.close()

    def export_shapefile(self):
       os.system('pgsql2shp -h '+hostDB+' -p '+portDB+' -u '+userDB+' -P '+passDB+' -f '+self.file_out+
                 ' '+nameDB+' "select * from '+self.nodes_table+', '+self.netwk_table+'"')

    def export_prop_json(self, gid, pid=''):
        if pid == '':
            pid = self.pid
        cur = self.conn.cursor()
        cur2 = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT array_to_string(ARRAY(SELECT c.column_name::text "
                    "FROM information_schema.columns As c "
                    "WHERE table_name = '"+self.nodes_table+"' "
                    "AND c.column_name NOT IN('geom')), ',')")
        self.cols = cur.fetchone()[0]
        cur2.execute("select "+self.cols+" from "+self.nodes_table+" where gid = %s", (gid,))
        jsondata = simplejson.dumps(cur2.fetchall(), use_decimal=True)
        jsondata = jsondata.replace('[', '').replace(']', '').replace('NaN', 'null')
        cur.close()
        cur2.close()
        return jsondata

    def export_geojson(self, where='', pid='', out=''):
        if pid != '':
            self.nodes_table = self.nodes_table + pid

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
        gj = open(out+'_nodes.json','w')
        gj.write(gjson)
        gj.close()

    def export_network_json(self):
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('select ordem, comprimento, grau_medio, coef_aglom_medio, diametro, densidade, strt_medio from '
                     +self.netwk_table)
        prop_geral = simplejson.dumps(cur.fetchall(), use_decimal=True, ignore_nan=True)
        prop_geral = prop_geral.replace('NaN','null')
        cur.close()
        gj = open(self.file_out + '_netwrk.json', 'w')
        gj.write(prop_geral)
        gj.close()

    def export_grafojson(self):
        #Dict of nodes
        cur2 = self.conn.cursor(cursor_factory=RealDictCursor)
        cur2.execute("select " + self.cols + " from " + self.nodes_table + " order by gid")
        results = cur2.fetchall()

        # Dict of edges
        cols = ('de','para')
        lista = []
        lista_conex = self.get_conex()
        for item in lista_conex:
            lista.append(dict(zip(cols, item)))

        # Puts together nodes and edges and dumps all as json
        grafodata = dict(labels=results, links=lista)
        jsondata = simplejson.dumps(grafodata, use_decimal=True, ignore_nan=True)
        jsondata = jsondata.replace('NaN','null')
        jg = open(self.file_out + '_grafo.json', 'w')
        jg.write(jsondata)
        jg.close()

    def export_ordered_json(self, order_cols, pid=''):
        if pid == '':
            pid = self.pid
        cur = self.conn.cursor()
        cur2 = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT array_to_string(ARRAY(SELECT c.column_name::text "
                    "FROM information_schema.columns As c "
                    "WHERE table_name = '"+self.nodes_table+"' "
                    "AND c.column_name NOT IN('geom')), ',')")
        self.cols = cur.fetchone()[0]
        for ord_col in order_cols:
            cur2.execute("select "+self.cols+" from "+self.nodes_table+" order by "+ord_col+" DESC nulls last limit 100")
            jsondata = simplejson.dumps(cur2.fetchall(), use_decimal=True, ignore_nan=True)
            jg = open(self.file_out + 'order_'+ord_col+'.json', 'w')
            jg.write(jsondata)
            jg.close()
        cur.close()
        cur2.close()
        return jsondata

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
        self.mencamList = None

        self.create_graph()
        #self.plot_graph()
        self.densidade = self.grafo.density()

    def create_graph(self):
        self.grafo = Graph(directed=self.directed)
        self.grafo.add_vertices(self.ordem)
        for itens in self.lista_conexoes:
            de, para = itens[0], itens[1]
            self.grafo.add_edges([(de-1, para-1)])

    def plot_graph(self):
        layout = self.grafo.layout("fr")
        visual_style = {}
        visual_style["vertex_size"] = 10
        plot(self.grafo, self.figura, layout=layout, bbox=(450, 300), **visual_style)

    def calculate_degree(self):
        global db
        grauList = self.grafo.degree()
        grauInList = self.grafo.degree(mode=IN)
        grauOutList = self.grafo.degree(mode=OUT)
        for i in range(self.ordem):
            grau = grauList[i]
            grau_in = grauInList[i]
            grau_out = grauOutList[i]
            db.update_grau_vertice(i+1, grau, grau_in, grau_out)
        db.conn.commit()
        self.grau_medio = sum(self.grafo.degree()) / self.ordem
        db.update_avg_degree(self.grau_medio)

    def clustering_coeff(self):
        global db
        i = 0
        for coef in self.grafo.transitivity_local_undirected():
            i += 1
            db.update_clustering_coeff(i, coef)
        db.conn.commit()
        self.coef_aglom_medio = self.grafo.transitivity_avglocal_undirected(mode="zero")
        db.update_avg_cluster_coeff(self.coef_aglom_medio)

    def avg_shortest_path(self):
        global db
        self.mencamList = []
        pool = mproc.Pool(processes=mproc.cpu_count())
        results = pool.map(self.shortest_path, range(self.ordem))
        i = 0
        for caminhoMed, mencam in results:
            db.update_avg_shortest_path(i+1, caminhoMed)
            self.mencamList.append(mencam)
            i += 1
        pool.close()
        db.conn.commit()
        diametro = self.grafo.diameter()
        db.update_diametro(diametro)
        self.diametro = diametro

    def shortest_path(self, i):
        mencam = self.grafo.shortest_paths_dijkstra(source=i)[0]
        caminhoMed = mean(mencam[x] for x in range(len(mencam)) if (mencam[x] != float('Inf')) and (mencam[x] != 0))
        return caminhoMed, mencam

    def plota_histograma(self):
        plt.hist(self.grafo.degree())
        plt.title("Histograma")
        plt.xlabel("Grau")
        plt.ylabel("Vertices")
        fig = plt.gcf()
        fig.set_size_inches(2.6, 2.2)
        fig.savefig(os.path.join(fnameout+'_hist.png'))

    def betweeness(self):
        global db
        lista_bet = self.grafo.betweenness()
        for i in range(0, len(lista_bet)):
            db.update_betweeness(i+1, lista_bet[i])
        db.conn.commit()

    def closeness(self):
        lista_cls = self.grafo.closeness()
        for i in range(0, len(lista_cls)):
            db.update_closeness(i+1, lista_cls[i])
        db.conn.commit()

    def eficiencia_global(self, g):
        sumMC = 0
        lenMC = 0
        for i in range(0, g.vcount()-1):
            mencam = g.shortest_paths_dijkstra(source=i)[0]
            invMencam = [1.0/x for x in mencam if (x!=float('Inf'))and(x!=0)]
            sumMC = sumMC + sum(invMencam)
            lenMC = lenMC + len(invMencam)

        eg = sumMC/lenMC
        return eg

    def vulnerabilidade(self):
        global db
        # Eficiencia com o vertice
        eg = self.eficiencia_global(self.grafo)
        # Eficiencia sem o vertice
        for i in range(0, self.ordem):
            g = self.grafo.copy()
            g.delete_vertices(i)
            efi = self.eficiencia_global(g)
            v = (eg-efi)/eg
            db.update_vulnerabilide(i+1, v)
        db.conn.commit()

    def straightness(self):
        global db
        pool2 = mproc.Pool(processes=mproc.cpu_count())
        results = pool2.map(self.straight_by_vertex, range(self.ordem))
        pool2.close()

        i = 0
        acc = 0
        nvert = 0
        for straight in results:
            db.update_straightness(i+1, straight)
            i += 1
            if straight != -1:
                acc+=straight
                nvert+=1
        avg_straight = acc/float(nvert)
        db.update_avg_straight(avg_straight)
        db.conn.commit()

    def straight_by_vertex(self, i):
        global db
        mencam = self.mencamList[i]
        nvert = 0
        sumV = 0
        euclDists = db.get_distance(i+1, range(1, self.ordem+1))
        for j in range(self.ordem):
            min_route = db.get_min_route_path(i + 1, j + 1)
            if j != i and min_route != None:
                euclDist = euclDists[j]
                min_route_km = float(min_route)/1000.
                ratio = (euclDist / min_route_km)
                if ratio > 1:
                    ratio = 1
                sumV += ratio
                nvert += 1
        if nvert != 0:
            strt = sumV / float(nvert)
        else:
            strt = -1
        return strt

class Shp2Graph:

    def __init__(self, fnamein, fnameout, pid, options, stream_field, basin_mouth):
        global db
        self.options = options.split(',')
        self.stream_field = stream_field
        self.basin_mouth = basin_mouth
        order_cols = []
        if self.options[0] == 'S':
            order_cols.append('grau')
        if self.options[1] == 'S':
            order_cols.append('coef_aglom')
        if self.options[2] == 'S':
            order_cols.append('mencamed')
        if self.options[3] == 'S':
            order_cols.append('betweeness')
        if self.options[4] == 'S':
            order_cols.append('closeness')
        if self.options[5] == 'S':
            order_cols.append('straight')

        print(datetime.datetime.now())
        file_type = os.path.splitext(fnamein)[-1]
        print(fnamein)
        print(file_type)
        db = Database(fnamein, fnameout, pid, file_type, options=self.options)
        print("Import realizado - "+str(datetime.datetime.now()))
        qv = db.get_qtd_registros()
        lc = db.get_conex()
        if file_type == '.osm':  # Cria grafo direcionado
            self.grf = Grafo(qv, lc, fnameout, True)
        else:
            self.grf = Grafo(qv, lc, fnameout)
        print("Grafo construido - " + str(datetime.datetime.now()))
        db.update_ordem_comp_densidade(self.grf.ordem, self.grf.comp, self.grf.densidade)

        self.realiza_calculos()
        print("Calculos realizados - " + str(datetime.datetime.now()))
        #self.grf.plota_histograma()
        db.export_shapefile()
        db.export_network_json()
        db.export_geojson()
        db.export_grafojson()
        db.export_ordered_json(order_cols=order_cols)
        self.compress_files(fnameout)
        #db.drop_tables()
        db.encerra_conexao()

    def realiza_calculos(self):
        global db
        if self.options[0] == 'S':
            self.grf.calculate_degree()
            print("> Grau calculado - "+str(datetime.datetime.now()))
        if self.options[1] == 'S':
            self.grf.clustering_coeff()
            print("> Coef. Aglom. calculado - "+str(datetime.datetime.now()))
        if self.options[2] == 'S':
            self.grf.avg_shortest_path()
            print("> Menor Caminho Médio calculado - "+str(datetime.datetime.now()))
        if self.options[3] == 'S':
            self.grf.betweeness()
            print("> Betweeness calculado - "+str(datetime.datetime.now()))
        if self.options[4] == 'S':
            self.grf.closeness()
            print("> Closeness calculado - " + str(datetime.datetime.now()))
        if self.options[5] == 'S':
            self.grf.straightness()
            print("> Straightness calculado - " + str(datetime.datetime.now()))
        if self.options[6] == 'S':
            self.grf.vulnerabilidade()
            print("> Vulnerabilidade calculada - " + str(datetime.datetime.now()))
        if self.options[7] == 'S':
            db.strahler(self.stream_field, self.basin_mouth)
            print("> Strahler calculado - " + str(datetime.datetime.now()))

    def compress_files(self, fnameout):
        zipf = zipfile.ZipFile(fnameout+'.zip', 'w', zipfile.ZIP_DEFLATED)
        files = (fnameout+'.dbf', fnameout+'.shp', fnameout+'.shx', fnameout+'.prj', fnameout+'_nodes.json',
                 fnameout+'_grafo.json', fnameout+'_netwrk.json', fnameout+'_grafo.png', fnameout+'_hist.png')
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
