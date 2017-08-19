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

    def __init__(self, file_in, file_out, pid):
        self.conn = None
        self.file_in = file_in
        self.file_out = file_out
        self.pid = str(pid.replace('-', ''))

        self.cria_database()
        self.importa_shapefile()
        self.mapeia_conexoes()

    def cria_database(self):
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

    def importa_shapefile(self):
        os.environ['PGPASSWORD'] = passDB
        os.system('shp2pgsql -s '+SRID+' -d -I -W "latin1" '+self.file_in+' public.s2g_nodes_'+self.pid+' | psql -h '+hostDB+' -p '+portDB+' -d '+nameDB+' -U '+userDB+' -w')
        cur = self.conn.cursor()
        cur.execute('alter table s2g_nodes_'+self.pid+' add column grau smallint')
        cur.execute('alter table s2g_nodes_'+self.pid+' add column coef_aglom numeric(6,2)')
        cur.execute('alter table s2g_nodes_'+self.pid+' add column mencamed character varying')
        cur.execute('alter table s2g_nodes_'+self.pid+' add column betweeness numeric(14,6)')
        cur.execute('alter table s2g_nodes_'+self.pid+' add column closeness numeric(6,4)')
        cur.close()
        self.conn.commit()

    def mapeia_conexoes(self):
        cur_de = self.conn.cursor()
        cur_para = self.conn.cursor()
        cur = self.conn.cursor()

        cur_de.execute('select gid from s2g_nodes_'+self.pid+' order by 1')
        for result_de in cur_de:
            id_trecho = result_de[0]
            cur_para.execute('select b.gid from s2g_nodes_'+self.pid+' a, s2g_nodes_'+self.pid+' b where st_intersects(a.geom, b.geom) and a.gid = %s and b.gid <> a.gid', (id_trecho,))
            for result_para in cur_para:
                conexao = result_para[0]
                if self.verifica_conexao(id_trecho, conexao) == False:
                    cur.execute('insert into s2g_conexoes_'+self.pid+' (de,para) values (%s,%s)', (id_trecho, conexao))
        self.conn.commit()

        cur_de.close()
        cur_para.close()
        cur.close()

    def verifica_conexao(self, id_trecho, conexao):
        existe = False
        cur = self.conn.cursor()
        cur.execute('select count(*) from s2g_conexoes_'+self.pid+' where (de = %s and para = %s) or (de = %s and para = %s)',(conexao,id_trecho,id_trecho,conexao))
        cont = int(cur.fetchone()[0])
        if cont > 0:
            existe = True
        cur.close()
        return existe

    def get_qtd_registros(self):
        cur = self.conn.cursor()
        cur.execute('select count(*) from s2g_nodes_'+self.pid)
        qtd_registros = cur.fetchone()[0]
        cur.close()
        return qtd_registros

    def get_conexoes(self):
        lista_conexoes = []
        cur = self.conn.cursor()
        cur.execute('select de, para from s2g_conexoes_'+self.pid+' inner join s2g_nodes_'+self.pid+' on de = gid')
        for result in cur:
            de, para = result[0], result[1]
            lista_conexoes.append((de, para))
        cur.close()
        return lista_conexoes

    def cria_tabela_geral(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists s2g_'+self.pid)
        self.conn.commit()

        cur.execute('create table s2g_'+self.pid+' ( \
                     ordem smallint, \
                     comprimento smallint, \
                     grau_medio numeric(6,2), \
                     coef_aglom_medio numeric(6,2), \
                     diametro smallint, \
                     densidade numeric(6,4))')
        self.conn.commit()
        cur.execute('insert into s2g_'+self.pid+' (ordem) values (0)')
        self.conn.commit()
        cur.close()

    def cria_tabela_conexoes(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists s2g_conexoes_'+self.pid)
        self.conn.commit()

        cur.execute('create table s2g_conexoes_'+self.pid+' ( \
                     id serial, \
                     de smallint, \
                     para smallint,'
                    'CONSTRAINT s2g_conex_'+self.pid+'_pkey PRIMARY KEY (id))')
        self.conn.commit()
        cur.close()

    def update_ordem_comp_densidade(self, ordem, comp, dens):
        cur = self.conn.cursor()
        cur.execute('update s2g_'+self.pid+' set ordem = %s, comprimento = %s, densidade = %s', (ordem, comp, dens))
        self.conn.commit()
        cur.close()

    def update_grau_vertice(self, id, grau):
        cur = self.conn.cursor()
        cur.execute('update s2g_nodes_'+self.pid+' set grau = %s where gid = %s', (grau, id))
        cur.close()

    def update_grau_medio(self, grau_medio):
        cur = self.conn.cursor()
        cur.execute('update s2g_'+self.pid+' set grau_medio = %s', (grau_medio, ))
        self.conn.commit()
        cur.close()

    def update_coef_aglomeracao(self, id, coef):
        cur = self.conn.cursor()
        cur.execute('update s2g_nodes_'+self.pid+' set coef_aglom = %s where gid = %s', (coef, id))
        cur.close()

    def update_coef_aglom_medio(self, coef):
        cur = self.conn.cursor()
        cur.execute('update s2g_'+self.pid+' set coef_aglom_medio = %s', (coef, ))
        self.conn.commit()
        cur.close()

    def update_menor_caminho_medio(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update s2g_nodes_'+self.pid+' set mencamed = %s where gid = %s', (valor, id))
        cur.close()

    def update_diametro(self, diametro):
        cur = self.conn.cursor()
        cur.execute('update s2g_'+self.pid+' set diametro = %s', (diametro,))
        self.conn.commit()
        cur.close()

    def update_betweeness(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update s2g_nodes_'+self.pid+' set betweeness = %s where gid = %s', (valor, id))
        cur.close()

    def update_closeness(self, id, valor):
        cur = self.conn.cursor()
        cur.execute('update s2g_nodes_'+self.pid+' set closeness = %s where gid = %s', (valor, id))
        cur.close()

    def encerra_conexao(self):
        self.conn.close()

    def exporta_shapefile(self):
       os.system('pgsql2shp -h '+hostDB+' -p '+portDB+' -u '+userDB+' -P '+passDB+' -f '+self.file_out+
                 ' '+nameDB+' "select * from s2g_nodes_'+self.pid+', s2g_'+self.pid+'"')

    def export_prop_json(self, gid):
        cur = self.conn.cursor()
        cols = ('gid', 'grau', 'coef_aglom', 'mencamed', 'betweeness', 'closeness')
        results = []
        cur.execute('select gid, grau, coef_aglom, mencamed, betweeness, closeness from s2g_nodes_'+self.pid+' where gid = %s', (gid,))
        result = cur.fetchone()
        results.append(dict(zip(cols, result)))
        jsondata = simplejson.dumps(results,use_decimal=True)
        jsondata = jsondata.replace('[','')
        jsondata = jsondata.replace(']','').replace('NaN','""')
        cur.close()
        return jsondata

    def export_geojson(self):
        cur = self.conn.cursor()
        cur.execute('select gid, st_asgeojson(geom) from s2g_nodes_'+self.pid+' order by gid')
        gjson = '{ "type": "FeatureCollection", "features": ['
        for result in cur:
            gid = result[0]
            prop_json = self.export_prop_json(gid)
            gjson = gjson+'{ "type": "Feature", "geometry": ' + result[1] + ', "properties": '+prop_json+'},'
        cur.close()
        gjson = gjson[0:-1] + ']}'
        gj = open(self.file_out+'.json','w')
        gj.write(gjson)
        gj.close()

    def export_txt(self):
        ft = open(self.file_out+'.txt','w')
        ft.write('----------\nLABELS\n---------\n')
        cur = self.conn.cursor()
        cur.execute('select gid, coef_aglom, mencamed, betweeness, closeness from s2g_nodes_'+self.pid+' order by gid')
        for result in cur:
            gid = str(result[0])
            coef_aglom = str(result[1])
            mencamed = str(result[2])
            betweeness = str(result[3])
            closeness = str(result[4])

            #nome = normalize('NFKD', nome).encode('ASCII','ignore').decode('ASCII')
            ft.write(gid+',Coef. Aglom: '+coef_aglom+'\\nMenor Caminho Medio: '+mencamed+'\\nBetweness: '+betweeness+
            '\\nCloseness: '+closeness+'\n')
        ft.write('------\nDADOS\n-----\n')
        lista_conex = self.get_conexoes()
        for item in lista_conex:
            de = item[0]
            para = item[1]
            ft.write(str(de)+','+str(para)+'\n')
        ft.close()

    def drop_tables(self):
        cur = self.conn.cursor()
        cur.execute('drop table if exists s2g_' + self.pid)
        cur.execute('drop table if exists s2g_nodes_' + self.pid)
        cur.execute('drop table if exists s2g_conexoes_' + self.pid)
        self.conn.commit()


class Grafo:

    def __init__(self, qtd_vertices, lista_conexoes, fnameout):
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

        self.cria_grafo()
        #self.plota_grafo()
        self.densidade = self.grafo.density()

    def cria_grafo(self):
        self.grafo = Graph()
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
        i = 0
        for grau in self.grafo.degree():
            i += 1
            db.update_grau_vertice(i, grau)
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
        for i in range(0, self.grafo.vcount()):
            db.update_betweeness(i+1, self.grafo.betweenness(vertices=i))
        db.conn.commit()
        for i in range(0, self.grafo.vcount()):
            db.update_closeness(i+1, self.grafo.closeness(vertices=i))
        db.conn.commit()


class Shp2Graph:

    def __init__(self, fnamein, fnameout, pid):
        print(datetime.datetime.now())
        db = Database(fnamein, fnameout, pid)
        print("import realizado - "+str(datetime.datetime.now()))
        qv = db.get_qtd_registros()
        lc = db.get_conexoes()
        self.grf = Grafo(qv, lc, fnameout)
        print("grafo construido - " + str(datetime.datetime.now()))
        db.update_ordem_comp_densidade(self.grf.ordem, self.grf.comp, self.grf.densidade)

        self.realiza_calculos(db)
        print("calc realizado - " + str(datetime.datetime.now()))
        #self.grf.plota_histograma()
        db.exporta_shapefile()
        db.export_geojson()
        db.export_txt()
        self.compress_files(fnameout)
        db.drop_tables()
        db.encerra_conexao()

    def realiza_calculos(self, db):
        self.grf.calcula_grau(db)
        print("Grau calculado - "+str(datetime.datetime.now()))
        self.grf.calcula_coef(db)
        print("Coef calculado - "+str(datetime.datetime.now()))
        self.grf.menor_caminho_medio(db)
        print("Men. Caminho calculado - "+str(datetime.datetime.now()))
        self.grf.centralidade(db)
        print("Centralidade calculada - "+str(datetime.datetime.now()))

    def compress_files(self, fnameout):
        zipf = zipfile.ZipFile(fnameout+'.zip', 'w', zipfile.ZIP_DEFLATED)
        files = (fnameout+'.dbf', fnameout+'.shp', fnameout+'.shx', fnameout+'.prj', fnameout+'.txt', fnameout+'.json',
            fnameout+'_grafo.png', fnameout+'_hist.png')
        for item in files:
            if os.path.exists(item):
                zipf.write(item)
        zipf.close()

if __name__ == '__main__':
    print(len(sys.argv))
    if len(sys.argv) == 4:
        fnamein = sys.argv[1]
        fnameout = sys.argv[2]
        pid = sys.argv[3]
        Shp2Graph(fnamein, fnameout, pid)
    else:
        print('Informar path do arquivo de entrada, path de saida e id do processo!')
        sys.exit()
