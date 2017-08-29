
var app = angular.module('gis4graph', ['ngRoute', 'ui-notification']);
app.config(function($routeProvider, $locationProvider, $sceDelegateProvider) {

	$routeProvider.when('/home', {
		templateUrl : 'view/home.html',
		controller : 'HomeController',
	}).when('/home/:msg', {
		templateUrl : 'view/home.html',
		controller : 'HomeController',

	}).when('/map/:id', {
		templateUrl : 'view/map.html',
		controller : 'MapController',
	}).when('/map/:id/:filter', {
		templateUrl : 'view/map.html',
		controller : 'MapController',

	}).when('/graph/:id', {
		templateUrl : 'view/graph.html',
		controller : 'GraphController',
	}).when('/graph/:id/:filter', {
		templateUrl : 'view/graph.html',
		controller : 'GraphController',

	}).otherwise({
		templateUrl : 'view/home.html',
		controller : 'HomeController'
	});

});


app.run(function() {
	//console.log('run');
});


