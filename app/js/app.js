
var app = angular.module('gis4graph', ['ngRoute', 'ui-notification']);
app.config(function($routeProvider, $locationProvider, $sceDelegateProvider) {

	$routeProvider.when('/home', {
		templateUrl : 'view/home.html',
		controller : 'HomeController',

	}).when('/map/:id', {
		templateUrl : 'view/map.html',
		controller : 'MapController',
	}).when('/map/:id/:filter', {
		templateUrl : 'view/map.html',
		controller : 'MapController',


	}).otherwise({
		templateUrl : 'view/home.html',
		controller : 'HomeController'
	});

});


app.run(function() {
	//console.log('run');
});


