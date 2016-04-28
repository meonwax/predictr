'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/bets', {
      templateUrl: 'templates/bets.html',
      controller: 'BetsCtrl',
      activeTab: 'bets',
      resolve: {
        groups: function($q, Group, $rootScope) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Group.query(function(groups) {
            deferred.resolve(groups);
          });
          return deferred.promise;
        }
      }
    });
  });
