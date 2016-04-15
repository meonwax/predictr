'use strict';

angular.module('predictrApp')
  .controller('LoginCtrl', function($scope, $location, Authentication) {

    $scope.credentials = {};

    $scope.login = function() {
      Authentication.login($scope.credentials)
        .then(function() {
          $scope.error = false;
          $location.path('');
        }, function(error) {
          $scope.error = true;
        })
    };
  });
