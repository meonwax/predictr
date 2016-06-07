'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider
      .when('/login', {
        templateUrl: 'templates/login.html',
        controller: 'LoginCtrl',
        activeTab: 'login'
      })
      .when('/register', {
        templateUrl: 'templates/register.html',
        controller: 'RegisterCtrl',
        activeTab: 'register'
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
