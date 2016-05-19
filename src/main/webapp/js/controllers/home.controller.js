'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($rootScope, $scope, upcomingGames, runningGames, shouts) {

    $rootScope.loading = false;

    // TODO: Read flag from config
    $scope.importantMessage = true;

    $scope.upcomingGames = upcomingGames;
    $scope.runningGames = runningGames;
    $scope.shouts = shouts;
  });
