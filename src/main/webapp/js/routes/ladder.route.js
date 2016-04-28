'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/ladder', {
      templateUrl: 'templates/ladder.html',
      controller: 'LadderCtrl',
      activeTab: 'ladder',
      resolve: {
        ladder: function($rootScope, $q, Ladder) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Ladder.ladder().all(function(ladder) {
            deferred.resolve(ladder);
          });
          return deferred.promise;
        },
        ladderJackpot: function($rootScope, $q, Ladder) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Ladder.ladder().jackpotOnly(function(ladderJackpot) {
            deferred.resolve(ladderJackpot);
          });
          return deferred.promise;
        },
        jackpot: function($rootScope, $q, $http) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          $http.get('api/users/jackpot').then(function(response) {
            deferred.resolve(response.data);
          });
          return deferred.promise;
        }
      }
    });
  });
