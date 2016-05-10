'use strict';

angular.module('predictrApp')
  .controller('AdminCtrl', function($rootScope, $scope, games, users) {
    $rootScope.loading = false;
    $scope.games = games;
    $scope.users = users;
  });
