
app.factory('DataFactory',function(){
	var extendedData = [];
	var g4gData = ['grau','grau_in','grau_out','betweeness','closeness','coef_aglom',
		'mencamed','straight','vulnerab'
	];
	var g4gLabels = ['Grau','Grau In','Grau Out','Betweeness','Closeness','Coef. Aglom.',
		'Min. Cam. Méd.','Straight','Vulnerab.'
	];
	var g4gSiglas = ['G','GI','GO','B','C','CA','MC','ST','VU'];
	
	var g4gAll = [];
	for (var i=0;i<g4gData.length;i++) {
		g4gAll.push({
			"data":g4gData[i],
			"label":g4gLabels[i],
			"sigla":g4gSiglas[i]
		});
	}
	//console.log(g4gAll);
	
	var limites = {};

	var limitesAll = {};
		
	return {
		getExtendedData: function() {
			return  extendedData;
		},
		setExtendedData: function(obj) {
			extendedData = [];
			for (var key in obj) {
				if (!(g4gData.indexOf(key)+1))
					extendedData.push(key);
			}
			return extendedData;
		},
		
		
		setLimits: function(obj,filtered) {
			for (var i=0;i<g4gData.length;i++) {
				if (limites[g4gData[i]].max < obj[g4gData[i]])
					limites[g4gData[i]].max = obj[g4gData[i]];
				if (limites[g4gData[i]].min > obj[g4gData[i]])
					limites[g4gData[i]].min = obj[g4gData[i]];

			}
			
			if (!filtered) 
				limitesAll = angular.copy(limites);
		},
		
		
		setFirstLimits:function(obj,filtered) {
			for (var i=0;i<g4gData.length;i++) {
				//console.log(obj);
				limites[g4gData[i]] = {
					max:0,min:0
				};
				
				limites[g4gData[i]].max = obj[g4gData[i]];
				limites[g4gData[i]].min = obj[g4gData[i]];
			}
			
			if (!filtered) 
				limitesAll = angular.copy(limites);

		},
		
		
		getLimits: function() {
			return limites;
		},
		getAllLimits: function() {
			return limitesAll;
		},
		
		getAll: function() {
			return g4gAll; 
		}
	};
});

app.controller('HomeController', function($scope, $http,$routeParams) {
	if ($routeParams.id)
		$scope.msg = $routeParams.msg;
	else
		$scope.msg = false;

	$scope.show = '';
	$scope.setShow = function(show) {
		$scope.show = show;
	};
});

app.controller('TabelaController', function($scope, $http,$routeParams, DataFactory) {
	$scope.all = DataFactory.getAll();
	$scope.results = [];
	$scope.labels = [];
	for (var i=0;i<$scope.all.length;i++) {
		//console.log(all[i]);
		url = HOST+'out/'+$routeParams.id+'/outorder_'+$scope.all[i].data+'.json';
		$http({
				method : 'GET',
				url : url
		}).then(function successCallback(r,r1) {
			var fTemp = r.config.url.match(/outorder_(.*?).json/g);
			var field = fTemp[0].slice(9,-5);
			$scope.results.push({
				"field":field,
				"data":r.data
			});
		}, function erroCallBack(r) {
			//console.log('erro',r);	
		});	
	}
	
	$scope.showTabela = function(b) {
		$scope.labels = [];
		for (var key in b.data[0]) {
			$scope.labels.push(key);
		}
		$scope.values = b.data;
	};
});


app.controller('GraphController', function($scope, $http, $routeParams, $location, $route , DataFactory) {
	
	var graph = Viva.Graph.graph();
	var container = document.body;
	var labels = [];
	$scope.g4g = DataFactory.getAll();
	
	var graphics = Viva.Graph.View.svgGraphics();
	var svgText = Viva.Graph.svg('text').attr('y', '-4px').attr('x',
						'4px').text('teste');
						
	$scope.showProp = {
		show: false,
		showMore: false,
		moreFields: [],
		ok: function() {
			$scope.showProp.show = false;
		},
		node: {}
	};
	
	
	var sizes = [];		
	var campoTam = $routeParams.field;
	
	
	//console.log(svgText);
	// This function let us override default node appearance and create
	// something better than blue dots:
	graphics.node(function(node) {
		// node.data holds custom object passed to graph.addNode():
		//console.log(node.data.obj[campoTam],campoTam);
		if (campoTam == 'mencamed') {
			if (node.data.obj[campoTam] <= sizes[0]) {
				var url = 'images/vermelho2.png';
			} else if (node.data.obj[campoTam] <= sizes[1]) {
				var url = 'images/vermelho.png';
			} else if (node.data.obj[campoTam] <= sizes[2]) {
				var url = 'images/verde.png';
			} else  {
				var url = 'images/no_foto2.png';
			}
			var tam = 100 - (node.data.obj[campoTam] * 100 / $scope.max );
			if (tam < 0) tam = 1;
			 
		} else {
			if (node.data.obj[campoTam] <= sizes[0]) {
				var url = 'images/no_foto2.png';
			} else if (node.data.obj[campoTam] <= sizes[1]) {
				var url = 'images/verde.png';
			} else if (node.data.obj[campoTam] <= sizes[2]) {
				var url = 'images/vermelho.png';
			} else  {
				var url = 'images/vermelho2.png';
			}
			var tam =  (node.data.obj[campoTam] * 100 / $scope.max );
			if (tam < 0) tam = 1; 
		}


		//console.log(node.data.obj[campoTam]); return true;

		var ui = Viva.Graph.svg('image').attr('width', 20 + tam).attr('height', 20 + tam).link(url);

		
		$(ui).click(function() {// mouse click
			$scope.showProp.show = true;
			$scope.showProp.node = node.data.obj;
			//console.log(node);
			$scope.$apply();
		});
		
		return ui;

	}); 


	var url = HOST+'out/'+$routeParams.id+'/';

	if ($routeParams.filter != undefined) {
		url += $routeParams.filter+'.json'; 
	} else {
		url += 'out_grafo.json'; 
	}
	
	$http({
		method : 'GET',
		url : url
	}).then(function successCallback(r) {
		//console.log(r);
		for (i=0;i < r.data.labels.length; i++) {
			if (i==0) {
				$scope.showProp.moreFields = DataFactory.setExtendedData(r.data.labels[i]);
				DataFactory.setFirstLimits(r.data.labels[i],false);
			} else {
				DataFactory.setLimits(r.data.labels[i],false);
			}
			
			node = r.data.labels[i];
			
			graph.addNode(node.gid, {
				id: node.gid,
				nome: JSON.stringify(node),
				img:'no_foto2.png',
				obj:node
			});

		};


		$scope.allLimites = DataFactory.getAllLimits();
		var max=$scope.allLimites[campoTam].max;
		var min=$scope.allLimites[campoTam].min;
		sizes[0] = (max - min) / 4;
		sizes[1] = (max - min) / 4 * 2;
		sizes[2] = (max - min) / 4 * 3;
		sizes[3] = (max - min);
		$scope.max = max;
		for (i=0;i < r.data.links.length; i++) {
			l = r.data.links[i];
			graph.addLink(l.de, l.para);
		}
		

		renderer = Viva.Graph.View.renderer(graph, {
			graphics : graphics
		});
		renderer.rerender();
		renderer.run();
	}, function(r) {
		console.log(r);
	});
});

app.controller('MapController', function($scope, $http, $routeParams,$location, Notification,DataFactory) {

	$scope.g4g = DataFactory.getAll();
	
	/*popup
	* 
	*/
	var container = document.getElementById('popup');
	var content = document.getElementById('popup-content');
	var closer = document.getElementById('popup-closer');


	/**
	 * Create an overlay to anchor the popup to the map.
	 */
	var overlay = new ol.Overlay(/** @type {olx.OverlayOptions} */( {
		element : container,
		autoPan : true,
		autoPanAnimation : {
			duration : 250
		}
	}));

	/**
	 * Add a click handler to hide the popup.
	 * @return {boolean} Don't follow the href.
	 */
	closer.onclick = function() {
		overlay.setPosition(undefined);
		closer.blur();
		return false;
	}; 
	/*
	 *  fim popup
	 */


	/*
	 * button download
	 * 
	 */
	var fctDownload  = function(opt_options) {

		var options = opt_options || {};

		var button = document.createElement('button');
		button.title = "Download";
		button.innerHTML = 'D';

		var this_ = this;
		var handleRotateNorth = function() {
			window.open(HOST+'out/'+$routeParams.id+'/out.zip');
		};

		button.addEventListener('click', handleRotateNorth, false);
		button.addEventListener('touchstart', handleRotateNorth, false);

		var element = document.createElement('div');
		element.className = 'rotate-north ol-unselectable ol-control';
		element.appendChild(button);

		ol.control.Control.call(this, {
			element : element,
			target : options.target
		});

	};
	ol.inherits(fctDownload, ol.control.Control); 

	/*
	 * fim button
	 */	
	

	var mousePositionControl = new ol.control.MousePosition({
		coordinateFormat : ol.coordinate.createStringXY(4),
		projection : 'EPSG:4326',
		// comment the following two lines to have the mouse position
		// be placed within the map.
		className : 'custom-mouse-position',
		target : document.getElementById('mouse-position'),
		undefinedHTML : '&nbsp;'
	}); 
      	
	var map = new ol.Map({
		controls : ol.control.defaults({
			attributionOptions : /** @type {olx.control.AttributionOptions} */( {
				collapsible : false
			})
		}).extend([new fctDownload(),mousePositionControl]),
		overlays : [overlay],
		target : 'map',
		layers : [new ol.layer.Tile({
			source : new ol.source.OSM()
		})],
		view : new ol.View({
			center : ol.proj.fromLonLat([-42.62, -22.34]),
			zoom : 8,
			rotation : 0
		})
	});


	/**
	* Add a click handler to the map to render the popup.
	*/
	map.on('singleclick', function(evt) {

		var feature = map.forEachFeatureAtPixel(evt.pixel, function(feature, layer) {
			return feature;
		});
		
		if (feature) {
			var txt = 
				'Coef. Aglom: '+feature.get('coef_aglom')+'<br>'+
				'Grau: '+feature.get('grau')+'<br>'+
				'Betweeness: '+feature.get('betweeness')+'<br>'+
				'Menor Cam. Médio: '+feature.get('mencamed')+'<br>'+
				'Closeness: '+feature.get('closeness')+'<br>'+
				'Straight: '+feature.get('straight')+'<br>'+
				'Vulnerab.: '+feature.get('vulnerab')+'<br>'+
				'Strahler:'+feature.get('strahler')+'<br>';

			for (var i=0;i<$scope.moreFields.length;i++) {
				txt += $scope.moreFields[i]+': '+feature.get($scope.moreFields[i])+'<br>';
			}
							
			
			var coordinate = evt.coordinate;
			var hdms = ol.coordinate.toStringHDMS(ol.proj.transform(coordinate, 'EPSG:3857', 'EPSG:4326'));
	
			content.innerHTML = '<p>Propriedades:</p><code>' +txt+ '</code>';
			overlay.setPosition(coordinate);
		}
	}); 


	/*
	map.on("move", function(e) {
		console.log('aqui');
		var position = e.map.getLonLatFromViewPortPx(e.xy);
		OpenLayers.Util.getElement("tooltip").innerHTML = "<label>Latitude: " + position.lat + "</label><br/><label>Longitude: " + position.lon + "</label>";
	});
	*/
	$scope.corPadrao = '#AAAAAA';
	$scope.cores = [];

	$scope.coresT = [
		"#00ffff",
		"#a52a2a",
		"#00008b",
		"#006400",
		"#bdb76b",
		"#8b008b",
		"#556b2f",
		"#ff8c00",
		"#9932cc",
		"#8b0000",
		"#e9967a",
		"#9400d3",
		"#ff00ff",
		"#ffd700",
		"#008000",
		"#4b0082",
		"#008b8b",
		"#f0e68c",
		"#add8e6",
		"#e0ffff",
		"#90ee90",
		"#d3d3d3",
		"#ffb6c1",
		"#ffffe0",
		"#00ff00",
		"#ff00ff",
		"#800000",
		"#000080",
		"#808000",
		"#ffa500",
		"#ffc0cb",
		"#800080",
		"#ff0000",
		"#c0c0c0",
		"#a9a9a9",
		"#ffffff",
		"#ffff00",
		"#f0ffff",
		"#0000ff",
		"#000000",
		
	];
	
	$scope.coresGrau = [];
				


	
	$scope.labels = {
		carregando : true,
		legenda: true
	};

	var url = HOST+'out/'+$routeParams.id+'/';
	if ($routeParams.filter != undefined) {
		url += $routeParams.filter+'.json'; 
	} else {
		url += 'out.json'; 
	}
	
	$http({
		method : 'GET',
		url : url
	}).then(function successCallback(r) {
		data = r.data;
		$scope.labels.carregando = false;
		$scope.moreFields = DataFactory.setExtendedData(r.data.features[0].properties);
		$scope.coresGrau[data.features[0].properties.grau] = $scope.corPadrao;
		DataFactory.setFirstLimits(data.features[0].properties,$routeParams.filter != undefined);
		

		for (var i=1;i<data.features.length;i++) {
			DataFactory.setLimits(data.features[i].properties,$routeParams.filter != undefined);
			$scope.coresGrau[data.features[i].properties.grau] = $scope.corPadrao;
		}
		$scope.limites = DataFactory.getLimits();
		$scope.allLimites = DataFactory.getAllLimits();
		
		//console.log($scope.coresGrau);
		iCor = 0;
		for (i=$scope.coresGrau.length - 1; i >= 0;i--) {
			if ($scope.coresGrau[i] === $scope.corPadrao) {
				//console.log($scope.coresGrau[i]);
				if ($scope.coresT[iCor] != undefined) {
					$scope.cores[i] = {cor: $scope.coresT[iCor],i:i,iCor:iCor};
					iCor++;
				} else {
					$scope.cores[i] = {cor: "#000000",i:i,iCor:0};
				}
			} else {
				$scope.cores[i] = {cor: false,i:i,iCor:0};
			}
		}
		
		//$scope.cores.reverse();
		//console.log($scope.cores);

		$scope.obj = data;
		addLayer();
		
	}, function errorCallback(r) {
		$scope.labels.carregando = false;
		Notification.warning(r);
	});
			

	function styleFunction(f) {
		if (is.null(f.R.grau)) {
			//console.log(f);
			cor = $scope.corPadrao;
		} else {
			cor = $scope.cores[f.R.grau].cor;
		}
		
		
		var st = new ol.style.Style({
			stroke : new ol.style.Stroke({
				color : cor,
				lineDash : [f.R.coef_aglom],
				width : 5
			}),
			fill : new ol.style.Fill({
				color : 'rgba(0, 0, 255, 0.1)'
			})
		});
		//console.log(st);
		return st;

	};

	function addLayer() {

		_geojson_vectorSource = new ol.source.Vector({
			features : (new ol.format.GeoJSON()).readFeatures($scope.obj, {
				featureProjection : 'EPSG:3857'
			})
		});

		_geojson_vectorLayer = new ol.layer.Vector({
			source : _geojson_vectorSource,
			style : styleFunction
		});

		map.addLayer(_geojson_vectorLayer); 
		
		map.getView().fit(_geojson_vectorSource.getExtent(), map.getSize());
		
	};


	/*
	 * FILTER
	 */
	
	$scope.filter = {
		show: false,
		showFilter: function() {
			$scope.filter.show = !$scope.filter.show;
			if ($scope.filter.show) {
				//
			}
		},
		filtrar: function() {
			var str = '';
			var strDiv = '';
			for (var i=0;i<$scope.g4g.length;i++) {
				str += strDiv+$scope.g4g[i].sigla+
					'_S'+$scope.limites[$scope.g4g[i].data].min+
					'_E'+$scope.limites[$scope.g4g[i].data].max
				;
				strDiv = '__';
			}
			/*
			console.log(str);
			str = 'CA_S'+$scope.limites.coef_aglom.min+'_E'+$scope.limites.coef_aglom.max+'__'+
				'G_S'+$scope.limites.grau.min+'_E'+$scope.limites.grau.max+'__'+
				'B_S'+$scope.limites.betweeness.min+'_E'+$scope.limites.betweeness.max+'__'+
				'MC_S'+$scope.limites.mencamed.min+'_E'+$scope.limites.mencamed.max+'__'+
				'C_S'+$scope.limites.closeness.min+'_E'+$scope.limites.closeness.max+'__';
			//console.log(str);
			*/
			$location.path('map/'+$routeParams.id+'/'+str);
		},
		original: function() {
			$location.path('map/'+$routeParams.id);
		}
	};

	/*
	 *  END FILTER
	 */

	$scope.grafo = {
		show: false,
		showOptions: function() {
			$scope.grafo.show = !$scope.grafo.show;
		},
		showGrafo : function(f) {
			//window.location.assign ('#/graph/'+$routeParams.id+'/'+f+'/'+$scope.limites[f].min+'/' +$scope.limites[f].max);
			//window.reload();
			//+'/'+$scope.allLimites[f].min+'/' +$scope.allLimites[f].max 
			window.open( '#/graph/'+$routeParams.id+'/'+f,'_blank');
		}
	};
	
	
	$scope.tabela = {
		showTabela: function() {
			window.open( '#/tabela/'+$routeParams.id,'_blank');
		}
	};
	
	


});


app.filter('reverse', function() {
  return function(items) {
    return items.slice().reverse();
  };
});