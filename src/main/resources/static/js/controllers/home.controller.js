'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($rootScope, $scope, upcomingGames, runningGames, shouts) {

    $rootScope.loading = false;

    $scope.upcomingGames = upcomingGames;
    $scope.runningGames = runningGames;
    $scope.shouts = shouts;
  });
