var cores =  [
		"#777777", 
		"#FFFF00",
		"#FFA500", 
		"#7CFC00", 
		"#00FFFF", 
		"#0000FF",
 		"#483D8B",
	];
	

app.directive('map', function() {
	return {
		template : '<div id="map"></div>',
		restrict : 'E',
		controller : function($scope) {

			$scope.map = L.map('map').setView([-22.7719332689999, -44.7020913539999], 10);

			

			var osm = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
				attribution : '<label id="labelLatLon">-22.771933, -44.702091</label>'
			}).addTo($scope.map);
			
			/*
			var satellite = L.tileLayer('http://{s}.{base}.maps.cit.api.here.com/maptile/2.1/maptile/{mapID}/satellite.day/{z}/{x}/{y}/256/png8?app_id={app_id}&app_code={app_code}', {
				attribution : 'Map &copy; 1987-2014 <a href="http://developer.here.com">HERE</a>',
				subdomains : '1234',
				mapID : 'newest',
				app_id : 'Y8m9dK2brESDPGJPdrvs',
				app_code : 'dq2MYIvjAotR8tHvY8Q_Dg',
				base : 'aerial',
				maxZoom : 20
			}).addTo($scope.map);
			*/

			var greenIcon = L.icon({
				iconUrl : 'img/fisl_icon.png',
				iconSize : [38, 38],
			});

			/*var marker = L.marker([-30.0577843,-51.1732458], {icon: greenIcon}).addTo($scope.map)
			 .bindPopup('<strong>Evento:</strong> FISL 16. <br> <strong>Local:</strong> PUCRS');
			 */
			var baseLayers = {
				'OpenStreetMap' : osm,
				//'SatelliteDay' : satellite,
				//'None': undefined
			};

			var overlayLayers = {
				// 'Brasil': $scope.brasil,
				//'Fisl16': marker
			};
			/*
			 baseLayers = {};
			 overlayLayers = {};
			 */


			$scope.control = L.control.layers(baseLayers, overlayLayers).addTo($scope.map);
			
			var legend = L.control({position: 'bottomright'});
			legend.onAdd = function(map) {
				var div = L.DomUtil.create('div', 'info legend'),
				    grades = [0, 10, 20, 50, 100, 200, 500, 1000,1,1],
				    labels = [];

				// loop through our density intervals and generate a label with a colored square for each interval
				for (var i = 0; i < cores.length; i++) {
					div.innerHTML += '<i style="background:' + cores[i] + '">___</i> Grau ' + i + '<br>';
					//console.log(cores[i]);
				}

				return div;
			};
			legend.addTo($scope.map);
			
			/*
			var legend2 = L.control({position: 'bottomright'});
			legend2.onAdd = function(map) {
				var div = L.DomUtil.create('div', 'info legend'),
				    grades = [0, 10, 20, 50, 100, 200, 500, 1000,1,1],
				    labels = [];

				// loop through our density intervals and generate a label with a colored square for each interval
				div.innerHTML += '<svg height="5" width="10"> <line x1="0" y1="0" x2="20" y2="0" style="stroke:rgb(255,0,0);stroke-width:5" /></svg> Menor Cam<br>';
				div.innerHTML += '<svg height="5" width="10"> <line x1="0" y1="0" x2="20" y2="0" style="stroke:rgb(255,0,0);stroke-width:22" /></svg> Maior Cam<br>';

				return div;
			};
			legend2.addTo($scope.map);
			*/

			$scope.map.addEventListener('mousemove', function(ev) {
			   lat = Math.round(ev.latlng.lat*1000000)/1000000;
			   lng = Math.round(ev.latlng.lng*1000000)/1000000;
			   document.getElementById('labelLatLon').innerHTML = lat + ','+lng + ' | Sig4Graph ';
			   //console.log(ev);
			});

		}
	};
});