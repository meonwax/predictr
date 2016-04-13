'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($rootScope, $scope, $http, Game, Shout) {

    // TODO: Read flag from config
    $scope.importantMessage = true;

    if ($rootScope.authenticated) {
      $scope.upcomingGames = Game.upcomingGames().get();
      $scope.runningGames = Game.runningGames().get();
      $scope.shouts = Shout.query({limit: 5});
    }

    $scope.credentials = {};

    // TODO: Replace $http with Account service
    // TODO: Replace HTTP Basic Auth
    $scope.login = function() {
      var headers = {authorization: 'Basic ' + btoa($scope.credentials.email + ':' + $scope.credentials.password)};
      $http.get('api/users/account', {headers: headers})
        .then(function(response) {
          if (response.data.name) {
            $rootScope.authenticated = true;
          } else {
            $rootScope.authenticated = false;
            $scope.error = true;
          }
        }, function() {
          $rootScope.authenticated = false;
          $scope.error = true;
        });
    };
  });
