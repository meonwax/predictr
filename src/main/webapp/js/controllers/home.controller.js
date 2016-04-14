'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($rootScope, $scope, $http, Authentication, Game, Shout) {

    // TODO: Read flag from config
    $scope.importantMessage = true;

    if (Authentication.getToken()) {
      $scope.upcomingGames = Game.upcomingGames().get();
      $scope.runningGames = Game.runningGames().get();
      $scope.shouts = Shout.query({limit: 5});
    }

    $scope.credentials = {};

    $scope.login = function() {
      Authentication.login($scope.credentials)
        .then(function() {
          $scope.success = true;
          $scope.error = false;
        }, function(error) {
          $scope.success = false;
          $scope.error = true;
        })
    };
  });
