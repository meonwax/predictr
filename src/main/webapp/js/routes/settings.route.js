'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/settings', {
      templateUrl: 'templates/settings.html',
      controller: 'SettingsCtrl',
      activeTab: 'settings'
      // resolve: {
      // }
    });
  });
