'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider
      .when('/login', {
        templateUrl: 'templates/login.html',
        controller: 'LoginCtrl',
        activeTab: 'login'
      })
      .when('/shoutbox', {
        templateUrl: 'templates/shoutbox.html',
        controller: 'ShoutboxCtrl',
        activeTab: 'shoutbox'
      })
      .when('/admin', {
        templateUrl: 'templates/admin.html',
        controller: 'AdminCtrl',
        activeTab: 'admin',
      })
      .otherwise({
        redirectTo: '/'
      });
  });
