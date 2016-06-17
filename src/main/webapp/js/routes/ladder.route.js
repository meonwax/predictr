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
        jackpot: function($rootScope, $q, Ladder) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Ladder.jackpot().get(function(jackpot) {
            deferred.resolve(jackpot.value);
          });
          return deferred.promise;
        },
        progress: function($rootScope, $q, Game) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Game.progress().get(function(progress) {
            deferred.resolve(progress);
          });
          return deferred.promise;
        }
      }
    });
  });
