'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($scope, Authentication, Game, Shout) {

    // TODO: Read flag from config
    $scope.importantMessage = true;

    if (Authentication.getToken()) {
      $scope.upcomingGames = Game.upcomingGames().get();
      $scope.runningGames = Game.runningGames().get();
      $scope.shouts = Shout.query({limit: 5});
    }
  });
