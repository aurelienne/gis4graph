app.controller('HomeController', function($scope, $http,$location) {
	$scope.verExemplo =  function () {
		console.log('aqui');
		$location.path('/map/7f81065533104ae38ef2f8975de036f1');
	};
});

app.controller('GraphController', function($scope, $http, $routeParams ) {
	var graph = Viva.Graph.graph();
	

	var graphics = Viva.Graph.View.svgGraphics();

	// This function let us override default node appearance and create
	// something better than blue dots:
	graphics.node(function(node) {
		// node.data holds custom object passed to graph.addNode():
		var url = 'images/' + node.data.img;
		var tam = (node.data.ocorrencias) * 1;
		if (tam > 200)
			tam = 200;
		var ui = Viva.Graph.svg('image').attr('width', 20 + tam).attr('height', 20 + tam).link(url);
		/*
		$(ui).click(function() {// mouse click
			console.log(node);
			alert(node.data.nome + ' (Grau: ' + node.data.grau + ') ');
		});
		*/
		return ui;
	});


	var url = '../out/'+$routeParams.id+'/';
	/*
	if (is.browser()) {
		var url = '../out/'+$routeParams.id+'/';
	} else {
		var url = 'http://35.195.102.228/out/'+$routeParams.id+'/';
	}
	*/
	if ($routeParams.filter != undefined) {
		url += $routeParams.filter+'.json'; 
	} else {
		url += 'out_grafo.json'; 
	}
	console.log(url);
	
	$http({
		method : 'GET',
		url : url
	}).then(function successCallback(r) {
		console.log(r);
		for (i=0;i < r.data.labels.length; i++) {
			node = r.data.labels[i];
			graph.addNode(node.gid, {
				id: node.gid,
				nome:'Coef. Aglom: 0.33\nMenor Caminho Medio: 84.27\nBetweness: 7074.000000\nCloseness: 0.0119\nRio Jaguari (ID 3)',
				img:'nofoto.jpg',
				ocorrencias:0
			});
		};
		
		for (i=0;i < r.data.links.length; i++) {
			l = r.data.links[i];
			graph.addLink(l.de, l.para);
		}
		

		renderer = Viva.Graph.View.renderer(graph, {
			graphics : graphics
		});
		renderer.run();
	}, function(r) {
		console.log(r);
	});
});

app.controller('MapController', function($scope, $http, $routeParams,$location, Notification) {

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
		button.innerHTML = 'D';

		var this_ = this;
		var handleRotateNorth = function() {
			window.open('../out/'+$routeParams.id+'/out.zip');
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
				'Strahler:'+feature.get('strahler')+'<br>'+
				'Gid: '+feature.get('gid')+'<br>';
			
			var coordinate = evt.coordinate;
			var hdms = ol.coordinate.toStringHDMS(ol.proj.transform(coordinate, 'EPSG:3857', 'EPSG:4326'));
	
			content.innerHTML = '<p>Propriedades:</p><code>' +txt+ '</code>';
			overlay.setPosition(coordinate);
		}
	}); 


	map.on("move", function(e) {
		console.log('aqui');
		var position = e.map.getLonLatFromViewPortPx(e.xy);
		OpenLayers.Util.getElement("tooltip").innerHTML = "<label>Latitude: " + position.lat + "</label><br/><label>Longitude: " + position.lon + "</label>";
	}); 

	$scope.cores = [
		"#777777", 
		"#FFFF00",
		"#FFA500", 
		"#7CFC00", 
		"#00FFFF", 
		"#0000FF",
 		"#483D8B",
	];
				
	$scope.limites = {
		coef_aglom:{max:0,min:0},
		grau:{max:0,min:0},
		betweeness:{max:0,min:0},
		mencamed:{max:0,min:0},
		closeness:{max:0,min:0},
		gid:{max:0,min:0},
		strahler:{max:0,min:0}
		
	};
	

	
	$scope.labels = {
		carregando : true,
		legenda: true
	};
	//var url = 'http://35.195.102.228/out/'+$routeParams.id+'/';
	var url = '../out/'+$routeParams.id+'/';
	if ($routeParams.filter != undefined) {
		url += $routeParams.filter+'.json'; 
	} else {
		url += 'out.json'; 
	}
	
	$http({
		method : 'GET',
		url : url
	}).then(function successCallback(r) {
		$scope.labels.carregando = false;
		data = r.data;
		//console.log(data);
		$scope.limites.coef_aglom.max = data.features[0].properties.coef_aglom;
		$scope.limites.coef_aglom.min = data.features[0].properties.coef_aglom;

		$scope.limites.grau.max = data.features[0].properties.grau;
		$scope.limites.grau.min = data.features[0].properties.grau;

		$scope.limites.betweeness.max = data.features[0].properties.betweeness;
		$scope.limites.betweeness.min = data.features[0].properties.betweeness;

		$scope.limites.mencamed.max = data.features[0].properties.mencamed;
		$scope.limites.mencamed.min = data.features[0].properties.mencamed;

		$scope.limites.closeness.max = data.features[0].properties.closeness;
		$scope.limites.closeness.min = data.features[0].properties.closeness;

		$scope.limites.gid.max = data.features[0].properties.gid;
		$scope.limites.gid.min = data.features[0].properties.gid;

		$scope.limites.strahler.max = data.features[0].properties.strahler;
		$scope.limites.strahler.min = data.features[0].properties.strahler;

		for (var i=1;i<data.features.length;i++) {
			/*
			if (data.features[i].properties.coef_aglom  == "") {
				console.log(data.features[i] );
			}
			*/
			if (data.features[i].properties.coef_aglom > $scope.limites.coef_aglom.max)
				$scope.limites.coef_aglom.max = data.features[i].properties.coef_aglom;  
			if (data.features[i].properties.coef_aglom < $scope.limites.coef_aglom.min)
				$scope.limites.coef_aglom.min = data.features[i].properties.coef_aglom;  

			if (data.features[i].properties.grau > $scope.limites.grau.max)
				$scope.limites.grau.max = data.features[i].properties.grau;  
			if (data.features[i].properties.grau < $scope.limites.grau.min)
				$scope.limites.grau.min = data.features[i].properties.grau;  

			if (data.features[i].properties.betweeness > $scope.limites.betweeness.max)
				$scope.limites.betweeness.max = data.features[i].properties.betweeness;  
			if (data.features[i].properties.betweeness < $scope.limites.betweeness.min)
				$scope.limites.betweeness.min = data.features[i].properties.betweeness;  


			/*
			if (data.features[i].properties.mencamed == Infinity)
				data.features[i].properties.mencamed = 0;
			*/
			if (data.features[i].properties.mencamed > $scope.limites.mencamed.max)
				$scope.limites.mencamed.max = parseFloat(data.features[i].properties.mencamed);  
			if (data.features[i].properties.mencamed < $scope.limites.mencamed.min)
				$scope.limites.mencamed.min = parseFloat( data.features[i].properties.mencamed);  

			if (data.features[i].properties.closeness > $scope.limites.closeness.max)
				$scope.limites.closeness.max = data.features[i].properties.closeness;  
			if (data.features[i].properties.closeness < $scope.limites.closeness.min)
				$scope.limites.closeness.min = data.features[i].properties.closeness;  

			if (data.features[i].properties.gid > $scope.limites.gid.max)
				$scope.limites.gid.max = data.features[i].properties.gid;  
			if (data.features[i].properties.gid < $scope.limites.gid.min)
				$scope.limites.gid.min = data.features[i].properties.gid;  
				
				
			if (data.features[i].properties.strahler > $scope.limites.strahler.max)
				$scope.limites.strahler.max = data.features[i].properties.strahler;  
			if (data.features[i].properties.strahler < $scope.limites.strahler.min)
				$scope.limites.strahler.min = data.features[i].properties.strahler;  
				

		}
		//console.log($scope.limites);
		$scope.obj = data;
		addLayer();
		
	}, function errorCallback(r) {
		$scope.labels.carregando = false;
		Notification.warning(r);
	});
			

	function styleFunction(f) {
		cor = $scope.cores[f.R.grau];
		
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
			str = 'CA_S'+$scope.limites.coef_aglom.min+'_E'+$scope.limites.coef_aglom.max+'__'+
				'G_S'+$scope.limites.grau.min+'_E'+$scope.limites.grau.max+'__'+
				'B_S'+$scope.limites.betweeness.min+'_E'+$scope.limites.betweeness.max+'__'+
				'MC_S'+$scope.limites.mencamed.min+'_E'+$scope.limites.mencamed.max+'__'+
				'C_S'+$scope.limites.closeness.min+'_E'+$scope.limites.closeness.max+'__';
			//console.log(str);
			$location.path('map/'+$routeParams.id+'/'+str);
		},
		original: function() {
			$location.path('map/'+$routeParams.id);
		}
	};

	/*
	 *  END FILTER
	 */

	$scope.showGrafo = function() {
		$location.path( 'graph/'+$routeParams.id );
		//window.location.redirect();
	}

});
