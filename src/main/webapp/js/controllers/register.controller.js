'use strict';

angular.module('predictrApp')
  .controller('RegisterCtrl', function($scope, $location, $translate, toastr, User, Authentication) {

    $scope.credentials = {};
    $scope.focusInput = true;

    $scope.register = function() {
      $scope.focusInput = false;

      // Try to register the new user
      User.register($scope.credentials)
        .then(function() {
          $scope.error = false;
          toastr.success($translate.instant('register.createOk'));

          // Login with created user
          Authentication.login($scope.credentials)
            .then(function() {
              $scope.error = false;
              $location.path('');
            }, function(error) {
              $scope.focusInput = true;
              $scope.error = true;
            });
        }, function(error) {
          $scope.focusInput = true;
          $scope.error = true;
        })
    };
  });
