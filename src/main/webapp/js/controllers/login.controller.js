'use strict';

angular.module('predictrApp')
  .controller('LoginCtrl', function($rootScope, $scope, $location, $translate, amMoment, Authentication, User) {

    // Redirect if already logged in
    if( $rootScope.account && $rootScope.account.id) {
      $location.path('');
    }

    $scope.credentials = {};
    $scope.focusInput = true;
    $rootScope.loading = false;

    $scope.login = function() {
      $scope.focusInput = false;
      $scope.sending = true;
      Authentication.login($scope.credentials)
        .then(function() {
          $scope.sending = false;
          $scope.error = false;
          User.account().get(function(user) {
            $translate.use(user.preferredLanguage);
            amMoment.changeLocale(user.preferredLanguage);
            $rootScope.account = user;
          });
          $location.path('');
        }, function(error) {
          $scope.sending = false;
          $scope.focusInput = true;
          $scope.error = true;
        });
    };
  });
