'use strict';

angular.module('predictrApp')
  .controller('LostPasswordCtrl', function($rootScope, $scope, $location, $translate, toastr, User) {

    // Redirect if already logged in
    if( $rootScope.account && $rootScope.account.id) {
      $location.path('');
    }

    $scope.focusInput = true;

    $scope.request = function() {
      $scope.focusInput = false;
      $scope.sending = true;

      User.resetPassword().save($scope.email,
        function() {
          $scope.error = false;
          $scope.sending = false;
          toastr.success($translate.instant('lostpwd.ok'), {timeOut: 5000});
          $location.path('login');
        },
        function() {
          $scope.sending = false;
          $scope.focusInput = true;
          $scope.error = true;
        }
      );
    };
  });
