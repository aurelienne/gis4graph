# GIS4Graph
<img src="http://marciorossato.com.br/app/images/logo.png" />

# About
GIS4Graph is an opensource software which aims to help analyzing geographic networks based on (geo)graphs - graphs in which the nodes have a known geographical location and the edges have spatial dependence (Santos et al., 2017). It has been developed to be used as a Web tool and it is composed of 3 modules:
1. Spatial Data Handling (Python class named Database);
2. Graph Metrics Calculation (Python class named Graph);
3. Results Visualization (Module based on python+flask, openlayers and angularJS)

In terms of geospatial data, GIS4Graph is able to work both with shapefiles and OpenStreetMap (OSM) files as input. When dealing with a shapefile, it must be a set of linestrings representing the network to be analyzed. Such data are then inserted into a database with geographic support - using PostgreSQL as the Database Management System and PostGIS as its spatial extension.  The connections identification between network segments is efficiently performed by an indexed spatial query based on a function that verifies intersections between geometric features. When it comes to an OSM file representing a street network, a PostgreSQL extension named pgRouting is employed. In both cases, the result is a connection list between nodes.
The very first step before any calculation is to build a graph based on the analyzed network. It can be done by adding a node for each geographic feature and edges based on the connection list. The igraph library is used for both graph building and some default metrics calculation. Vertex degree, clustering coefficient, shortest paths and betweenness are some examples of metrics calculated by igraph and incorporated to G4G. The resultant dataset is displayed visually on a map or as a graph.

# How to execute
1. Execute runflask script to start Flask Server (edit runflask to indicate the network port to be used to start Flask server);
2. Access it (locally) via browser at: http://localhost/app/index.html

# Requirements
Python 3.0+ and libs: igraph, simplejson, flask, psycopg2, configparser, multiprocess<Br>
PostgreSQL 9.1+<br>
PostGIS <Br>
PGRouting <br>
osm2pgrouting

# License
This project is licensed under the terms of the GNU GPL v3.0

# Developers 
Aurelienne Jorge (aurelienne@gmail.com) 
Marcio Rossato (marcioarp@gmail.com)

# Online version
Available at: http://gis4graph.info or http://gis4graph.com

# References
Santos, L. B. L.; Jorge, A. A. S.; Rossato, M.; Santos, J. D.; Candido, O. A.; Seron, W.;
Santana, C. N. (2017): (geo)graphs - Complex Networks as a shapefile of nodes and
a shapefile of edges for different applications. To be submitted.
