'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider
      .when('/login', {
        templateUrl: 'templates/login.html',
        controller: 'LoginCtrl'
      })
      .when('/register', {
        templateUrl: 'templates/register.html',
        controller: 'RegisterCtrl'
      })
      .when('/lostpwd', {
        templateUrl: 'templates/lostpwd.html',
        controller: 'LostPasswordCtrl'
      })
      .when('/settings', {
        templateUrl: 'templates/settings.html',
        controller: 'SettingsCtrl',
        activeTab: 'settings'
      })
      .otherwise({
        redirectTo: '/'
      });
  });
