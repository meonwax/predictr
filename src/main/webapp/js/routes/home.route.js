'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/', {
      templateUrl: 'templates/home.html',
      controller: 'HomeCtrl',
      activeTab: 'home',
      resolve: {
        upcomingGames: function($rootScope, $q, Game) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Game.upcomingGames().get(function(upcomingGames) {
            deferred.resolve(upcomingGames);
          });
          return deferred.promise;
        },
        runningGames: function($rootScope, $q, Game) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Game.runningGames().get(function(runningGames) {
            deferred.resolve(runningGames);
          });
          return deferred.promise;
        },
        shouts: function($rootScope, $q, Shout) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Shout.query({limit: 5}, function(shouts) {
            deferred.resolve(shouts);
          });
          return deferred.promise;
        }
      }
    });
  });
