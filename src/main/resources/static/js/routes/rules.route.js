'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/rules', {
      templateUrl: 'templates/rules.html',
      controller: 'RulesCtrl',
      activeTab: 'rules',
      resolve: {
        rules: function($rootScope, $q, $translate, ServerInfo) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          var currentLanguage = $translate.use() || $translate.preferredLanguage();
          ServerInfo.get().get(function(serverInfo) {
            deferred.resolve(serverInfo.rules[currentLanguage]);
          });
          return deferred.promise;
        }
      }
    });
  });
