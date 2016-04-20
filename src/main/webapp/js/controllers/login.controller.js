'use strict';

angular.module('predictrApp')
  .controller('LoginCtrl', function($scope, $location, Authentication) {

    $scope.credentials = {};
    $scope.focusInput = true;

    $scope.login = function() {
      $scope.focusInput = false;
      Authentication.login($scope.credentials)
        .then(function() {
          $scope.error = false;
          $location.path('');
        }, function(error) {
          $scope.focusInput = true;
          $scope.error = true;
        })
    };
  });
