'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/rules', {
      templateUrl: 'templates/rules.html',
      controller: 'RulesCtrl',
      activeTab: 'rules',
      resolve: {
        rules: function($q, $http, $translate) {
          var deferred = $q.defer();
          var currentLanguage = $translate.use() || $translate.preferredLanguage();
          $http.get('values/rules-' + currentLanguage + '.md').then(function(response) {
            deferred.resolve(response.data);
          });
          return deferred.promise;
        }
      }
    });
  });
