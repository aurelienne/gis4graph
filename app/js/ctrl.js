app.controller('HomeController', function($scope, $http) {

});

app.controller('MapController', function($scope, $http, $routeParams) {
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
	
	$http({
		method : 'GET',
		url : '../out/'+$routeParams.id+'/out.json'
	}).then(function successCallback(r) {
		data = r.data;
		console.log(data);
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
				$scope.limites.mencamed.max = data.features[i].properties.mencamed;  
			if (data.features[i].properties.mencamed < $scope.limites.mencamed.min)
				$scope.limites.mencamed.min = data.features[i].properties.mencamed;  

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
		console.log($scope.limites);
		$scope.obj = data;
		addLayer();
		
	}, function errorCallback(r) {
		console.log(r);
	});
			

	function styleFeature(f) {
		//console.log(f);
		cor = $scope.cores[f.properties.grau];
		 
		
		var wh = 10;//(10 * (f.properties.mencamed / $scope.limites.mencamed.max ));

		return {
			fillColor : cor,
			fillOpacity : 0.7,
			color : cor,
			opacity : 0.7,//(f.properties.betweeness / $scope.limites.betweeness.max)+0.1,
			weight : wh,
			dashArray : f.properties.coef_aglom,
		};
	};

	function addLayer() {
		//console.log(obj);
		$scope.brasil = L.geoJson($scope.obj, {
			style : styleFeature,
			onEachFeature : onEachFeature,
			filter : filter
		});
		$scope.brasil.addTo($scope.map);
		$scope.map.fitBounds($scope.brasil.getBounds());
		$scope.control.addOverlay($scope.brasil, 'GIS4Graph');
	}

	/*Function that zoom map on selected feature
	 called on onEachFeature -> layer.on({click})*/
	function zoomToFeature(e) {
		$scope.map.fitBounds(e.target.getBounds());
	}

	function onEachFeature(feature, layer) {
		//console.log(feature);
		layer.bindPopup(
			'Coef. Aglom: '+feature.properties.coef_aglom+'<br>'+
			'Grau: '+feature.properties.grau+'<br>'+
			'Betweeness: '+feature.properties.betweeness+'<br>'+
			'Menor Cam. Médio: '+feature.properties.mencamed+'<br>'+
			'Closeness: '+feature.properties.closeness+'<br>'+
			'Strahler:'+feature.properties.strahler+'<br>'+
			'Gid: '+feature.properties.gid+'<br>'
		);
		layer.on({
			//mouseover: highlightFeature,
			//mouseout: resetHighlight,
			//click: zoomToFeature
		});
	}

	function filter(feature, layer) {
		//console.log(feature);
		if (feature.properties.id <= $scope.numero)
			return true;
		return true;
	};

});

