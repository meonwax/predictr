'use strict';

angular.module('predictrApp')
  .controller('LoginCtrl', function($rootScope, $scope, $location, $translate, amMoment, Authentication, User) {

    $scope.credentials = {};
    $scope.focusInput = true;
    $rootScope.loading = false;

    $scope.login = function() {
      $scope.focusInput = false;
      Authentication.login($scope.credentials)
        .then(function() {
          $scope.error = false;
          User.account().get(function(user) {
            $translate.use(user.preferredLanguage);
            amMoment.changeLocale(user.preferredLanguage);
            $rootScope.account = user;
          });
          $location.path('');
        }, function(error) {
          $scope.focusInput = true;
          $scope.error = true;
        });
    };
  });
