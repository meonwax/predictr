'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($scope, upcomingGames, runningGames, shouts) {

    // TODO: Read flag from config
    $scope.importantMessage = true;

    $scope.upcomingGames = upcomingGames;
    $scope.runningGames = runningGames;
    $scope.shouts = shouts;
  });
