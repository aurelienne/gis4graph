

var app = angular.module('gis4graph', ['ngRoute', 'ui-notification']);
app.config(function($routeProvider, $locationProvider, $sceDelegateProvider) {

	$routeProvider.when('/home', {
		templateUrl : 'view/home01.html',
		controller : 'HomeController',
	}).when('/home/:msg', {
		templateUrl : 'view/home01.html',
		controller : 'HomeController',

	}).when('/map/:id', {
		templateUrl : 'view/map004.html',
		controller : 'MapController',
	}).when('/map/:id/:filter', {
		templateUrl : 'view/map004.html',
		controller : 'MapController',

	}).when('/tabela/:id', {
		templateUrl : 'view/tabela002.html',
		controller : 'TabelaController',

	}).when('/graph/:id/:field', {
		cache: false,
		templateUrl : 'view/graph002.html',
		controller : 'GraphController',

	}).otherwise({
		templateUrl : 'view/home01.html',
		controller : 'HomeController'
	});

});


app.run(function() {
	//console.log('run');
});


