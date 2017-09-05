
var app = angular.module('gis4graph', ['ngRoute', 'ui-notification']);
app.config(function($routeProvider, $locationProvider, $sceDelegateProvider) {

	$routeProvider.when('/home', {
		templateUrl : 'view/home.html',
		controller : 'HomeController',
	}).when('/home/:msg', {
		templateUrl : 'view/home.html',
		controller : 'HomeController',

	}).when('/map/:id', {
		templateUrl : 'view/map001.html',
		controller : 'MapController',
	}).when('/map/:id/:filter', {
		templateUrl : 'view/map001.html',
		controller : 'MapController',

	}).when('/graph/:id/:field/:min/:max', {
		cache: false,
		templateUrl : 'view/graph001.html',
		controller : 'GraphController',

	}).otherwise({
		templateUrl : 'view/home.html',
		controller : 'HomeController'
	});

});


app.run(function() {
	//console.log('run');
});


